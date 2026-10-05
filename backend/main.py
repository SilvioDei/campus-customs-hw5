"""FastAPI backend for the Campus Customs dashboard.

Start it from the backend/ folder:

    uvicorn main:app --reload --port 8000

Shop data is read through the Campus Customs MCP tools (in-process MCP client).
Payments only happen in POST /payments/{id}/approve, which calls the human-only
approve_and_pay path; agents can only create pending requests.
"""

import asyncio
import importlib.util
import json
import shutil
import sys
from pathlib import Path

# Started as `uvicorn main:app` from backend/, this file is a top-level module,
# so put the project root on sys.path to import the backend package.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Query  # noqa: E402
from fastapi.concurrency import run_in_threadpool  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastmcp import Client  # noqa: E402

from backend.config import AUDIT_TRAIL_PATH, MCP_SERVER_SCRIPT, ORIGINAL_DB_PATH, WORKING_DB_PATH  # noqa: E402
from backend.models import ApprovePaymentBody  # noqa: E402


def _load_shop_server():
    """Import mcp_server/server.py by path (it is a script, not a package)."""
    spec = importlib.util.spec_from_file_location("campus_customs_mcp_server", MCP_SERVER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shop = _load_shop_server()

app = FastAPI(title="Campus Customs backend")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

_team = None
_busy = asyncio.Lock()  # one agent run or reset at a time


async def call_tool(name: str, args: dict | None = None) -> dict:
    """Call a Campus Customs MCP tool through an in-process MCP client."""
    async with Client(shop.mcp) as client:
        result = await client.call_tool(name, args or {}, raise_on_error=False)
    if result.is_error:
        raise HTTPException(502, f"MCP tool {name} failed: {result.content[0].text}")
    return result.structured_content


@app.get("/")
async def health() -> dict:
    return {"status": "ok", "working_db": WORKING_DB_PATH.name}


@app.get("/tickets")
async def list_tickets() -> dict:
    """Every ticket with its status and whether it is open or resolved."""
    tickets = (await call_tool("list_tickets"))["tickets"]
    return {"tickets": [{**t, "state": "resolved" if t["status"] == "resolved" else "open"} for t in tickets]}


@app.post("/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int) -> dict:
    """Run the agent team on one ticket (calls the model through Portkey)."""
    global _team
    ticket = await call_tool("get_ticket", {"ticket_id": ticket_id})
    if "error" in ticket:
        raise HTTPException(404, ticket["error"])
    if _busy.locked():
        raise HTTPException(409, "Another agent run or reset is in progress.")
    async with _busy:
        if _team is None:
            from backend.agents import Team  # built on first run so the server starts without a key
            _team = Team()
        result = await _team.run_ticket(ticket_id)
    # A finished run resolves the ticket only if every payment it needs has a
    # pending (or paid) request; the MCP tool enforces that rule. Payments stay
    # pending until a human approves them. Runs that hit a limit stay open.
    if "summary" in result:
        update = await call_tool("update_ticket_status", {"ticket_id": ticket_id, "status": "resolved"})
        if "error" in update:
            result["ticket_state"] = "open"
            result["unresolved_reason"] = update["error"]
        else:
            result["ticket_state"] = "resolved"
    return result


@app.get("/events")
def recent_events(
    limit: int = Query(50, ge=1, le=1000),
    ticket_id: int | None = None,
    run_id: str | None = None,
) -> dict:
    """Most recent audit-trail entries (oldest first), optionally for one ticket or run."""
    if not AUDIT_TRAIL_PATH.exists() or AUDIT_TRAIL_PATH.stat().st_size == 0:
        return {"events": [], "total": 0}
    entries = json.loads(AUDIT_TRAIL_PATH.read_text(encoding="utf-8"))
    if ticket_id is not None:
        entries = [e for e in entries if e.get("ticket_id") == ticket_id]
    if run_id is not None:
        entries = [e for e in entries if e.get("run_id") == run_id]
    recent = entries[-limit:]
    return {
        "total": len(entries),
        "events": [
            {**e, "said": e.get("summary", ""), "tools_used": [c["tool"] for c in e.get("tool_calls", [])]}
            for e in recent
        ],
    }


@app.get("/payments")
async def payment_requests(status: str = Query("pending", pattern="^(pending|paid|rejected|all)$")) -> dict:
    """Payment requests the agents prepared (pending by default), for the approve buttons.

    Each request gets a `payee` (who the money is for), looked up through MCP.
    """
    requests = (await call_tool("list_payment_requests", {"status": status}))["requests"]
    for r in requests:
        r["payee"] = await _payee(r)
    return {"requests": requests}


async def _payee(r: dict) -> str | None:
    if r["kind"] == "purchase_order":
        return (r.get("details") or {}).get("vendor_name")
    if r["kind"] == "invoice":
        info = await call_tool("get_invoice_status", {"invoice_id": r["ref_id"]})
        return info.get("invoice", {}).get("vendor_name")
    if r["kind"] == "rent":
        info = await call_tool("get_rent_status", {"lease_id": r["ref_id"]})
        return info.get("lease", {}).get("landlord")
    return None


@app.post("/payments/{request_id}/approve")
async def approve_payment(request_id: int, body: ApprovePaymentBody) -> dict:
    """A human approved this pending request: pay it. The only route that changes cash."""
    result = await run_in_threadpool(shop.approve_and_pay, request_id, body.approved_by)
    if "error" in result:
        msg = result["error"]
        code = 404 if msg.startswith("No payment request") else 400 if "named human" in msg else 409
        raise HTTPException(code, msg)
    return result


@app.get("/cash")
async def checking_balance() -> dict:
    """Current checking balance from cash_accounts."""
    accounts = (await call_tool("get_cash_position"))["cash_accounts"]
    checking = next((a for a in accounts if a["name"] == "checking"), None)
    if checking is None:
        raise HTTPException(404, "No checking account in cash_accounts.")
    return {"account": "checking", "balance": checking["balance"], "date": checking["date"],
            "pending_requests_total": checking["pending_requests_total"],
            "balance_after_pending": checking["balance_after_pending"]}


@app.post("/reset")
async def reset_database() -> dict:
    """Copy the original database over the working copy. The original is only read."""
    if _busy.locked():
        raise HTTPException(409, "An agent run is in progress; reset after it finishes.")
    async with _busy:
        await run_in_threadpool(shutil.copyfile, ORIGINAL_DB_PATH, WORKING_DB_PATH)
    return {"reset": True, "copied_from": ORIGINAL_DB_PATH.name, "copied_to": WORKING_DB_PATH.name}
