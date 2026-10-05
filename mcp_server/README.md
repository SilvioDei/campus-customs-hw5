# Campus Customs MCP Server

A FastMCP server that gives every agent on the Campus Customs team (Boss, Inventory, Accounting, Facilities, Customer Service) the same set of shop tools. Agents get facts from these tools instead of guessing, and every answer comes straight from the database. The backend agents connect to it as MCP clients over stdio.

## Database

The server uses the working copy `data/campus_customs_new.db`. The original `data/campus_customs.db` is never opened, so the working copy can be reset from it at any time. "Today" always comes from `desk.date_today`.

Read tools open the database read-only. The first write creates two extra tables in the working copy: `payment_requests` (pending payments waiting on a human) and `drafts` (unsent messages). Resetting the working copy removes them.

## Tools

### Read

| Tool | Inputs | What it returns |
|---|---|---|
| `get_today` | — | `desk.date_today` and desk notes. |
| `list_open_tickets` | — | Every ticket that isn't resolved. |
| `list_tickets` | — | Every ticket, including resolved ones, with its status (used by the dashboard). |
| `get_ticket` | `ticket_id` | One ticket with its linked SKU/size, lease, and invoice. |
| `get_invoice_status` | `invoice_id` | The invoice and its vendor (name, specialty, lead days), days overdue versus `date_today`, the vendor's open invoices, and whether the vendor is blocked from shipping. |
| `get_rent_status` | `lease_id` | The lease (rent, landlord, next due date), days until rent is due, an overdue flag, and the cash balances, including whether cash covers the rent. |
| `check_stock_and_pricing` | `sku`, `size`, `qty`, optional `discount_pct` | Stock on hand, the shortfall against the requested quantity, unit cost and list price, the margin at list price and at the proposed discount, and the largest discount possible before a loss. |
| `list_vendors` | — | Each vendor's specialty, lead time, open invoices, shipping block, and expected arrival if ordered today. |
| `list_open_invoices` | — | All open invoices with days overdue and the total owed. |
| `get_cash_position` | — | Cash balances, the total of pending payment requests, and the balance left if all of them were paid. |
| `list_payment_requests` | optional `status` | Payment requests (pending by default). |

### Write (no money moves)

| Tool | Inputs | What it does |
|---|---|---|
| `request_payment` | `kind` (invoice/rent), `ref_id`, `requested_by`, `reason`, optional `ticket_id`, `account` | Creates a **pending** request. The amount comes from the invoice or lease. Refuses if it is more than the balance or if a duplicate is already pending. |
| `request_purchase_order` | `vendor_id`, `sku`, `size`, `qty`, `requested_by`, `reason`, optional `ticket_id`, `account` | Creates a **pending** restock request for qty × unit_cost and warns if the vendor is blocked by an open invoice. |
| `save_draft_message` | `author_agent`, `recipient`, `subject`, `body`, optional `ticket_id` | Saves a draft on the board. Never sent. |
| `update_ticket_status` | `ticket_id`, `status` | Sets the status to open, in_progress, waiting_on_human, or resolved. |

That is all 15 MCP tools. None of them can move money.

### Human-only actions (not MCP tools)

These are plain Python functions in `server.py` without `@mcp.tool`, so no MCP client (no agent, and not the IDE's MCP client) can list or call them. Only the human approval path (the dashboard, in a later problem) calls them after a person approves.

| Function | Inputs | What it does |
|---|---|---|
| `approve_and_pay` | `request_id`, `approved_by` | Pays a pending request after a named human approves it. Refuses if the approver is blank or an agent, if the vendor on a purchase order still has an open invoice, or if the balance would go negative. On success it adds a `payments` row, lowers the cash balance, and marks the invoice paid or moves the lease's `next_due` forward one month. |
| `reject_payment_request` | `request_id`, `decided_by`, optional `note` | Rejects a pending request. |

## Run

```bash
.venv/Scripts/python.exe mcp_server/server.py
```
