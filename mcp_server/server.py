"""Campus Customs MCP server.

Exposes shop tools to the agent team. Every tool uses the working copy
data/campus_customs_new.db; the original campus_customs.db is never touched.

Most tools are read-only. The write tools only record pending payment requests,
customer/landlord drafts, and ticket status. No MCP tool can move money.

Paying happens only in approve_and_pay (and rejecting in reject_payment_request)
at the bottom of this file. They are plain functions, not MCP tools, so no MCP
client can call them; only the human approval path does. approve_and_pay needs
a named human approver and refuses if cash would go negative.
"""

import calendar
import json
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"

AGENT_NAMES = {"boss", "inventory", "accounting", "facilities", "customer_service"}
TICKET_STATUSES = ("open", "in_progress", "waiting_on_human", "resolved")

mcp = FastMCP("campus-customs")


def _connect(write: bool = False) -> sqlite3.Connection:
    """Open the working database (read-only unless write=True)."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Working database not found: {DB_PATH}")
    mode = "rw" if write else "ro"
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    if write:
        _ensure_side_tables(conn)
    return conn


def _ensure_side_tables(conn: sqlite3.Connection) -> None:
    """Tables for pending payment requests and drafts.

    They live only in the working copy, so resetting it from campus_customs.db
    clears them along with everything else.
    """
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS payment_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            ref_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            account TEXT NOT NULL,
            ticket_id INTEGER,
            requested_by TEXT NOT NULL,
            reason TEXT NOT NULL,
            details TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            decided_by TEXT,
            decided_at TEXT,
            decision_note TEXT,
            payment_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            author_agent TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL
        );
        """
    )


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def _shop_today(conn: sqlite3.Connection) -> date:
    """The shop's 'today' comes from desk.date_today, not the real clock.

    Every date the server writes (payment requests, decisions, drafts, payments)
    uses it too, so records line up with the shop's calendar.
    """
    row = conn.execute("SELECT date_today FROM desk").fetchone()
    return date.fromisoformat(row["date_today"])


def _pending_total(conn: sqlite3.Connection, account: str) -> float:
    if not _table_exists(conn, "payment_requests"):
        return 0.0
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM payment_requests "
        "WHERE status = 'pending' AND account = ?",
        (account,),
    ).fetchone()
    return float(row["total"])


def _add_one_month(d: date) -> date:
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return d.replace(year=year, month=month, day=min(d.day, calendar.monthrange(year, month)[1]))


@mcp.tool
def get_today() -> dict:
    """Return the shop's 'today' (desk.date_today) and any desk notes."""
    with closing(_connect()) as conn:
        row = conn.execute("SELECT date_today, notes FROM desk").fetchone()
    return dict(row)


@mcp.tool
def list_open_tickets() -> dict:
    """List every ticket that is not resolved, oldest first."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM tickets WHERE status != 'resolved' ORDER BY created_at"
        ).fetchall()
    return {"tickets": [dict(r) for r in rows]}


@mcp.tool
def list_tickets() -> dict:
    """List every ticket, including resolved ones, with its current status."""
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()
    return {"tickets": [dict(r) for r in rows]}


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """Return one ticket with its linked SKU/size, lease_id, and invoice_id, plus
    the payments it needs before it can be resolved and whether each already has
    a pending (or paid) payment request."""
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"error": f"No ticket with id {ticket_id}."}
        required = _required_payments(conn, row)
    return {"ticket": dict(row), "required_payments": required,
            "can_resolve": all(r["has_request"] for r in required)}


def _required_payments(conn: sqlite3.Connection, ticket: sqlite3.Row) -> list[dict]:
    """Payments a ticket needs a request for before it counts as resolved.

    - A linked open invoice (tickets.invoice_id) needs an invoice request.
    - A linked lease (tickets.lease_id) needs a rent request.
    Purchase orders are a judgment call, so they are never required.
    A request counts if it is pending or already paid.
    """
    needed = []
    if ticket["invoice_id"] is not None:
        inv = conn.execute("SELECT amount, status FROM invoices WHERE id = ?", (ticket["invoice_id"],)).fetchone()
        if inv is not None and inv["status"] == "open":
            needed.append(("invoice", ticket["invoice_id"], inv["amount"]))
    if ticket["lease_id"] is not None:
        lease = conn.execute("SELECT monthly_rent FROM leases WHERE id = ?", (ticket["lease_id"],)).fetchone()
        if lease is not None:
            needed.append(("rent", ticket["lease_id"], lease["monthly_rent"]))
    out = []
    for kind, ref_id, amount in needed:
        req = None
        if _table_exists(conn, "payment_requests"):
            req = conn.execute(
                "SELECT id, status FROM payment_requests WHERE kind = ? AND ref_id = ? "
                "AND status IN ('pending', 'paid') ORDER BY id DESC",
                (kind, ref_id),
            ).fetchone()
        out.append({"kind": kind, "ref_id": ref_id, "amount": amount, "has_request": req is not None,
                    "request_id": req["id"] if req else None, "request_status": req["status"] if req else None})
    return out


@mcp.tool
def get_invoice_status(invoice_id: int) -> dict:
    """Look up a vendor invoice and whether it blocks that vendor from shipping.

    Returns the invoice, the vendor's name and lead time, days overdue relative
    to the shop's date_today, and whether the vendor is blocked (a vendor will
    not ship new product while it has any open unpaid invoice).
    """
    with closing(_connect()) as conn:
        today = _shop_today(conn)
        inv = conn.execute(
            """
            SELECT i.id, i.vendor_id, i.amount, i.due_date, i.status, i.description,
                   v.name AS vendor_name, v.specialty AS vendor_specialty,
                   v.lead_days AS vendor_lead_days
            FROM invoices i JOIN vendors v ON v.id = i.vendor_id
            WHERE i.id = ?
            """,
            (invoice_id,),
        ).fetchone()
        if inv is None:
            return {"error": f"No invoice with id {invoice_id}."}

        open_invoices = conn.execute(
            "SELECT id, amount FROM invoices WHERE vendor_id = ? AND status = 'open'",
            (inv["vendor_id"],),
        ).fetchall()

    days_past_due = (today - date.fromisoformat(inv["due_date"])).days
    is_open = inv["status"] == "open"
    return {
        "shop_today": today.isoformat(),
        "invoice": dict(inv),
        "is_open": is_open,
        "is_overdue": is_open and days_past_due > 0,
        "days_overdue": max(days_past_due, 0) if is_open else 0,
        "vendor_open_invoices": [dict(r) for r in open_invoices],
        "vendor_blocked_from_shipping": len(open_invoices) > 0,
    }


@mcp.tool
def get_rent_status(lease_id: int) -> dict:
    """Look up a lease's rent amount and due date against the shop's date_today.

    Returns the lease, days until rent is due (negative if overdue), and the
    current cash balance so Facilities can see whether rent is covered.
    """
    with closing(_connect()) as conn:
        today = _shop_today(conn)
        lease = conn.execute("SELECT * FROM leases WHERE id = ?", (lease_id,)).fetchone()
        if lease is None:
            return {"error": f"No lease with id {lease_id}."}
        accounts = conn.execute("SELECT name, balance, date FROM cash_accounts").fetchall()

    days_until_due = (date.fromisoformat(lease["next_due"]) - today).days
    total_cash = sum(a["balance"] for a in accounts)
    return {
        "shop_today": today.isoformat(),
        "lease": dict(lease),
        "days_until_due": days_until_due,
        "is_overdue": days_until_due < 0,
        "cash_accounts": [dict(a) for a in accounts],
        "cash_covers_rent": total_cash >= lease["monthly_rent"],
    }


@mcp.tool
def check_stock_and_pricing(sku: str, size: str, qty: int, discount_pct: float = 0.0) -> dict:
    """Check stock for a SKU and size against a requested quantity, with margins.

    Returns on-hand quantity, shortfall, unit cost, list price, and the margin
    at list price and at an optional proposed discount percentage (0-100).
    """
    if qty <= 0:
        return {"error": "qty must be a positive integer."}
    if not 0 <= discount_pct < 100:
        return {"error": "discount_pct must be between 0 and 100."}

    with closing(_connect()) as conn:
        item = conn.execute(
            "SELECT * FROM inventory WHERE sku = ? AND size = ?", (sku, size)
        ).fetchone()
        if item is None:
            return {"error": f"No inventory row for sku {sku} size {size}."}
        price = conn.execute("SELECT * FROM pricing WHERE sku = ?", (sku,)).fetchone()

    result = {
        "inventory": dict(item),
        "requested_qty": qty,
        "on_hand": item["qty"],
        "shortfall": max(qty - item["qty"], 0),
        "can_fill_from_stock": item["qty"] >= qty,
    }
    if price is None:
        result["pricing"] = None
        return result

    unit_cost, list_price = price["unit_cost"], price["list_price"]
    discounted_price = round(list_price * (1 - discount_pct / 100), 2)
    result["pricing"] = {
        "unit_cost": unit_cost,
        "list_price": list_price,
        "margin_per_unit_at_list": round(list_price - unit_cost, 2),
        "margin_pct_at_list": round((list_price - unit_cost) / list_price * 100, 1),
        "discount_pct": discount_pct,
        "unit_price_at_discount": discounted_price,
        "margin_per_unit_at_discount": round(discounted_price - unit_cost, 2),
        "margin_pct_at_discount": round((discounted_price - unit_cost) / discounted_price * 100, 1),
        "order_total_at_discount": round(discounted_price * qty, 2),
        "order_margin_at_discount": round((discounted_price - unit_cost) * qty, 2),
        "max_discount_pct_before_loss": round((1 - unit_cost / list_price) * 100, 1),
    }
    return result


@mcp.tool
def list_vendors() -> dict:
    """List every vendor with specialty, lead time, and open invoices.

    A vendor with any open unpaid invoice is blocked from shipping new product.
    expected_arrival_if_ordered_today is desk.date_today plus lead_days.
    """
    with closing(_connect()) as conn:
        today = _shop_today(conn)
        vendors = conn.execute("SELECT * FROM vendors ORDER BY id").fetchall()
        result = []
        for v in vendors:
            open_inv = conn.execute(
                "SELECT id, amount, due_date, description FROM invoices "
                "WHERE vendor_id = ? AND status = 'open'",
                (v["id"],),
            ).fetchall()
            result.append({
                **dict(v),
                "open_invoices": [dict(r) for r in open_inv],
                "blocked_from_shipping": len(open_inv) > 0,
                "expected_arrival_if_ordered_today": date.fromordinal(
                    today.toordinal() + v["lead_days"]
                ).isoformat(),
            })
    return {"shop_today": today.isoformat(), "vendors": result}


@mcp.tool
def list_open_invoices() -> dict:
    """List all open vendor invoices with days overdue versus desk.date_today."""
    with closing(_connect()) as conn:
        today = _shop_today(conn)
        rows = conn.execute(
            """
            SELECT i.*, v.name AS vendor_name, v.lead_days AS vendor_lead_days
            FROM invoices i JOIN vendors v ON v.id = i.vendor_id
            WHERE i.status = 'open' ORDER BY i.due_date
            """
        ).fetchall()
    invoices = []
    for r in rows:
        past_due = (today - date.fromisoformat(r["due_date"])).days
        invoices.append({**dict(r), "is_overdue": past_due > 0, "days_overdue": max(past_due, 0)})
    return {
        "shop_today": today.isoformat(),
        "invoices": invoices,
        "total_open": round(sum(i["amount"] for i in invoices), 2),
    }


@mcp.tool
def get_cash_position() -> dict:
    """Cash balances, money already earmarked by pending payment requests, and
    what would remain if every pending request were paid. No money comes in."""
    with closing(_connect()) as conn:
        accounts = conn.execute("SELECT name, balance, date FROM cash_accounts").fetchall()
        result = []
        for a in accounts:
            pending = _pending_total(conn, a["name"])
            result.append({
                **dict(a),
                "pending_requests_total": round(pending, 2),
                "balance_after_pending": round(a["balance"] - pending, 2),
            })
    return {"cash_accounts": result}


def _validate_account(conn: sqlite3.Connection, account: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM cash_accounts WHERE name = ?", (account,)).fetchone()


def _insert_request(conn, kind, ref_id, amount, account, ticket_id, requested_by, reason, details):
    dup = conn.execute(
        "SELECT id FROM payment_requests WHERE kind = ? AND ref_id = ? AND status = 'pending'",
        (kind, ref_id),
    ).fetchone()
    if dup is not None and kind != "purchase_order":
        return {"error": f"A pending {kind} request for {ref_id} already exists (request {dup['id']})."}
    cur = conn.execute(
        """
        INSERT INTO payment_requests
            (kind, ref_id, amount, account, ticket_id, requested_by, reason, details, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """,
        (kind, ref_id, amount, account, ticket_id, requested_by, reason,
         json.dumps(details) if details else None, _shop_today(conn).isoformat()),
    )
    return {"request_id": cur.lastrowid}


@mcp.tool
def request_payment(
    kind: Literal["invoice", "rent"],
    ref_id: int,
    requested_by: str,
    reason: str,
    ticket_id: int | None = None,
    account: str = "checking",
) -> dict:
    """Create a PENDING request to pay a vendor invoice (ref_id = invoice id) or
    rent (ref_id = lease id). This does not move money: a human must approve it.

    The amount is taken from the database (invoice amount or monthly rent), never
    from the caller. Refuses if the amount is more than the account balance.
    """
    with closing(_connect(write=True)) as conn, conn:
        acct = _validate_account(conn, account)
        if acct is None:
            return {"error": f"No cash account named {account}."}
        if kind == "invoice":
            row = conn.execute("SELECT * FROM invoices WHERE id = ?", (ref_id,)).fetchone()
            if row is None:
                return {"error": f"No invoice with id {ref_id}."}
            if row["status"] != "open":
                return {"error": f"Invoice {ref_id} is {row['status']}, not open."}
            amount = row["amount"]
        else:
            row = conn.execute("SELECT * FROM leases WHERE id = ?", (ref_id,)).fetchone()
            if row is None:
                return {"error": f"No lease with id {ref_id}."}
            amount = row["monthly_rent"]
        if amount > acct["balance"]:
            return {"error": f"Refused: {kind} {ref_id} costs {amount}, but {account} only has {acct['balance']}."}
        pending_before = _pending_total(conn, account)
        made = _insert_request(conn, kind, ref_id, amount, account, ticket_id, requested_by, reason, None)
        if "error" in made:
            return made
    after = round(acct["balance"] - pending_before - amount, 2)
    return {
        "request_id": made["request_id"],
        "status": "pending",
        "kind": kind,
        "ref_id": ref_id,
        "amount": amount,
        "account": account,
        "balance": acct["balance"],
        "balance_after_all_pending": after,
        "pending_exceeds_cash": after < 0,
        "note": "Waiting on human approval. No money has moved.",
    }


@mcp.tool
def request_purchase_order(
    vendor_id: int,
    sku: str,
    size: str,
    qty: int,
    requested_by: str,
    reason: str,
    ticket_id: int | None = None,
    account: str = "checking",
) -> dict:
    """Create a PENDING purchase-order payment request to restock a SKU/size.

    The amount is qty x pricing.unit_cost from the database. This does not move
    money: a human must approve it. The response warns if the vendor is blocked
    by an open unpaid invoice (it will not ship until that is paid).
    """
    if qty <= 0:
        return {"error": "qty must be a positive integer."}
    with closing(_connect(write=True)) as conn, conn:
        acct = _validate_account(conn, account)
        if acct is None:
            return {"error": f"No cash account named {account}."}
        vendor = conn.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
        if vendor is None:
            return {"error": f"No vendor with id {vendor_id}."}
        item = conn.execute(
            "SELECT 1 FROM inventory WHERE sku = ? AND size = ?", (sku, size)
        ).fetchone()
        price = conn.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (sku,)).fetchone()
        if item is None or price is None:
            return {"error": f"No inventory/pricing for sku {sku} size {size}."}
        amount = round(price["unit_cost"] * qty, 2)
        if amount > acct["balance"]:
            return {"error": f"Refused: PO costs {amount}, but {account} only has {acct['balance']}."}
        open_inv = conn.execute(
            "SELECT id FROM invoices WHERE vendor_id = ? AND status = 'open'", (vendor_id,)
        ).fetchall()
        pending_before = _pending_total(conn, account)
        details = {"vendor_name": vendor["name"], "sku": sku, "size": size, "qty": qty,
                   "unit_cost": price["unit_cost"], "lead_days": vendor["lead_days"]}
        made = _insert_request(conn, "purchase_order", vendor_id, amount, account,
                               ticket_id, requested_by, reason, details)
    after = round(acct["balance"] - pending_before - amount, 2)
    return {
        "request_id": made["request_id"],
        "status": "pending",
        "kind": "purchase_order",
        "amount": amount,
        "details": details,
        "vendor_blocked_by_invoices": [r["id"] for r in open_inv],
        "balance_after_all_pending": after,
        "pending_exceeds_cash": after < 0,
        "note": "Waiting on human approval. No money has moved.",
    }


@mcp.tool
def list_payment_requests(status: Literal["pending", "paid", "rejected", "all"] = "pending") -> dict:
    """List payment requests (default: only pending ones waiting on a human)."""
    with closing(_connect()) as conn:
        if not _table_exists(conn, "payment_requests"):
            return {"requests": []}
        sql = "SELECT * FROM payment_requests"
        rows = conn.execute(sql + ("" if status == "all" else " WHERE status = ?") + " ORDER BY id",
                            () if status == "all" else (status,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["details"] = json.loads(d["details"]) if d["details"] else None
        out.append(d)
    return {"requests": out}


@mcp.tool
def save_draft_message(
    author_agent: str, recipient: str, subject: str, body: str, ticket_id: int | None = None
) -> dict:
    """Save a draft message to a customer or landlord on the board. Drafts are
    never sent; a human reviews them."""
    with closing(_connect(write=True)) as conn, conn:
        cur = conn.execute(
            "INSERT INTO drafts (ticket_id, author_agent, recipient, subject, body, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'draft', ?)",
            (ticket_id, author_agent, recipient, subject, body, _shop_today(conn).isoformat()),
        )
    return {"draft_id": cur.lastrowid, "status": "draft", "sent": False}


@mcp.tool
def update_ticket_status(
    ticket_id: int, status: Literal["open", "in_progress", "waiting_on_human", "resolved"]
) -> dict:
    """Set a ticket's status on the board (open, in_progress, waiting_on_human, resolved).

    Refuses 'resolved' while a payment the ticket needs (see get_ticket's
    required_payments) has no pending or paid payment request.
    """
    with closing(_connect(write=True)) as conn, conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"error": f"No ticket with id {ticket_id}."}
        if status == "resolved":
            missing = [r for r in _required_payments(conn, row) if not r["has_request"]]
            if missing:
                need = ", ".join(f"{r['kind']} {r['ref_id']} (${r['amount']:,.2f})" for r in missing)
                return {"error": f"Refused: ticket {ticket_id} can't be resolved until it has a pending "
                                 f"payment request for: {need}.", "missing_payment_requests": missing}
        conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
    return {"ticket_id": ticket_id, "status": status}


# ---- Human-only actions --------------------------------------------------
# These are deliberately NOT MCP tools (no @mcp.tool), so no MCP client -- no
# agent, and not the IDE's MCP client through .mcp.json -- can list or call them. Only
# the human approval path (the dashboard's approve/reject buttons, in a later
# problem) imports and calls them, after a person clicks approve.


def approve_and_pay(request_id: int, approved_by: str) -> dict:
    """HUMAN ONLY. Pay a pending request after a named person approves it.

    Refuses if the request is not pending, if approved_by is empty or an agent,
    if a purchase-order vendor still has an open invoice, or if the account
    balance would go negative. On success it records the payment, lowers the
    cash balance, and updates the linked invoice (paid) or lease (next_due).
    """
    approver = approved_by.strip()
    if not approver or approver.lower().replace(" ", "_") in AGENT_NAMES:
        return {"error": "Refused: a named human must approve payments."}
    with closing(_connect(write=True)) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        req = conn.execute("SELECT * FROM payment_requests WHERE id = ?", (request_id,)).fetchone()
        if req is None:
            return {"error": f"No payment request with id {request_id}."}
        if req["status"] != "pending":
            return {"error": f"Request {request_id} is {req['status']}, not pending."}
        acct = _validate_account(conn, req["account"])
        if acct is None:
            return {"error": f"No cash account named {req['account']}."}
        if req["amount"] > acct["balance"]:
            return {"error": f"Refused: {req['amount']} would overdraw {req['account']} "
                             f"(balance {acct['balance']}). No negative balances."}
        if req["kind"] == "invoice":
            inv = conn.execute("SELECT status FROM invoices WHERE id = ?", (req["ref_id"],)).fetchone()
            if inv is None or inv["status"] != "open":
                return {"error": f"Invoice {req['ref_id']} is no longer open."}
        if req["kind"] == "purchase_order":
            blocking = conn.execute(
                "SELECT id FROM invoices WHERE vendor_id = ? AND status = 'open'", (req["ref_id"],)
            ).fetchall()
            if blocking:
                return {"error": "Refused: vendor will not ship while invoice(s) "
                                 f"{[r['id'] for r in blocking]} are unpaid. Pay those first."}

        today = _shop_today(conn).isoformat()
        new_balance = round(acct["balance"] - req["amount"], 2)
        cur = conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (req["kind"], req["ref_id"], req["amount"], req["account"], today, approver),
        )
        conn.execute("UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?",
                     (new_balance, today, req["account"]))
        updated = {"cash_accounts": {"name": req["account"], "balance": new_balance}}
        if req["kind"] == "invoice":
            conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (req["ref_id"],))
            updated["invoices"] = {"id": req["ref_id"], "status": "paid"}
        elif req["kind"] == "rent":
            lease = conn.execute("SELECT next_due FROM leases WHERE id = ?", (req["ref_id"],)).fetchone()
            next_due = _add_one_month(date.fromisoformat(lease["next_due"])).isoformat()
            conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (next_due, req["ref_id"]))
            updated["leases"] = {"id": req["ref_id"], "next_due": next_due}
        conn.execute(
            "UPDATE payment_requests SET status = 'paid', decided_by = ?, decided_at = ?, "
            "payment_id = ? WHERE id = ?",
            (approver, _shop_today(conn).isoformat(), cur.lastrowid, request_id),
        )
    return {"paid": True, "payment_id": cur.lastrowid, "request_id": request_id,
            "amount": req["amount"], "approved_by": approver, "updated": updated}


def reject_payment_request(request_id: int, decided_by: str, note: str = "") -> dict:
    """HUMAN ONLY. Reject a pending payment request. No money moves."""
    decider = decided_by.strip()
    if not decider or decider.lower().replace(" ", "_") in AGENT_NAMES:
        return {"error": "Refused: a named human must decide payment requests."}
    with closing(_connect(write=True)) as conn, conn:
        req = conn.execute("SELECT status FROM payment_requests WHERE id = ?", (request_id,)).fetchone()
        if req is None:
            return {"error": f"No payment request with id {request_id}."}
        if req["status"] != "pending":
            return {"error": f"Request {request_id} is {req['status']}, not pending."}
        conn.execute(
            "UPDATE payment_requests SET status = 'rejected', decided_by = ?, decided_at = ?, "
            "decision_note = ? WHERE id = ?",
            (decider, _shop_today(conn).isoformat(), note, request_id),
        )
    return {"rejected": True, "request_id": request_id, "decided_by": decider}


if __name__ == "__main__":
    mcp.run()
