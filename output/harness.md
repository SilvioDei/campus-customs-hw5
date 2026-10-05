# Campus Customs Harness

Contents: database tables · MCP tools (Problem 3, then the full list) · the five agents · safety and guardrails · backend API routes · dashboard.

## Database tables

Source: `data/campus_customs.db` (original, read-only). Agents work against `data/campus_customs_new.db`.

| Table | Fields | Why it matters for the agents |
|---|---|---|
| `desk` | date_today, notes | Defines "today" for the shop, so every overdue and due-soon check uses this date instead of the real clock. |
| `tickets` | id, type, requester, subject, sku, size, qty, lease_id, invoice_id, status, notes, created_at | The work queue: Boss reads each open ticket and routes it, and the sku/size, lease_id, and invoice_id fields link it to the other tables. |
| `inventory` | sku, name, size, qty, location | Inventory checks stock by SKU and size (primary key) to spot shortfalls before an order is promised. |
| `pricing` | sku, unit_cost, list_price | Accounting uses cost vs. list price to check margins on discount requests and to price restock purchase orders. |
| `vendors` | id, name, specialty, lead_days | Inventory matches a shortfall to a vendor by specialty and uses lead_days to estimate when restocked product arrives. |
| `invoices` | id, vendor_id, amount, due_date, status, description | Shows what the shop owes each vendor; an open invoice blocks that vendor from shipping and is a candidate payment for approval. |
| `leases` | id, space_name, landlord, monthly_rent, next_due, notes | Facilities tracks rent amount and due date for the shop space. |
| `cash_accounts` | name, balance, date | The cash available for payments; the pay tool must refuse anything that would make the balance negative. |
| `payments` | id, kind, ref_id, amount, account, paid_at, approved_by | The audit log of approved payments; every payment records what it paid (kind + ref_id) and who approved it. |

## MCP tools

Server: `mcp_server/server.py` (FastMCP). Database: `data/campus_customs_new.db`. All three tools are read-only.

| Tool | Tables it reads | Ticket it unlocks | Why it is the right tool for that ticket |
|---|---|---|---|
| `get_invoice_status(invoice_id)` | invoices, vendors, desk | 101 (Bulldog tee, size S) | Ticket 101 links to invoice 501, an open $840 Bulldog Print Co invoice that was due 2026-08-28 and is now 3 days overdue; because a vendor won't ship while an invoice is open, this tool shows the S tee can't be restocked (5-day lead time) until Accounting gets approval to pay 501. |
| `get_rent_status(lease_id)` | leases, desk, cash_accounts | 102 (rent notice) | Ticket 102 links to lease 1, and this tool confirms from the database, not the landlord's email, that $2,400 rent for the Chapel Street shop is due 2026-09-02 (2 days from date_today, so not yet overdue) and that the $3,400 checking balance covers it. |
| `check_stock_and_pricing(sku, size, qty, discount_pct)` | inventory, pricing | 103 (Yale AI Club bulk hoodie discount) | Ticket 103 asks for 20 CC-HOOD-NAVY in size M at a discount, and this tool shows only 8 are on hand (a 12-unit shortfall) and gives the $22 cost vs. $58 list margin at any proposed discount, so Accounting can price a discount that stays profitable. It also confirms ticket 101's S tee has 0 on hand. |

## Agent team

Built with PydanticAI in `backend/`. Every agent uses the one model set in `backend/config.py`, through Portkey with `PORTKEY_API_KEY` from `.env`. Each agent is an MCP client of `mcp_server/server.py` and only sees the MCP tools on the "Tools:" line of its prompt file in `backend/prompts/`. Every agent also has `delegate(to_agent, task)`, so any agent can hand work to any other agent (full connectivity).

| Agent | Prompt file | Job | MCP tools it can use |
|---|---|---|---|
| Boss | `boss.md` | Reads each ticket, routes it, flags anything involving money for a human, makes the final call on competing needs, and returns a `TicketSummary` (decision, who did what, what's waiting on a human). | get_today, list_open_tickets, get_ticket, get_cash_position, list_payment_requests, update_ticket_status |
| Inventory | `inventory.md` | Checks stock by SKU and size, reports needed / on hand / gap, finds the restock vendor and lead time, and sends open invoices that block a vendor to Accounting. | get_today, get_ticket, check_stock_and_pricing, list_vendors, get_invoice_status |
| Accounting | `accounting.md` | Prepares payments and purchase orders as pending requests only, never lets cash go negative, checks margins before discounts, and ranks payments when cash can't cover everything. | get_today, get_ticket, get_cash_position, list_open_invoices, get_invoice_status, get_rent_status, check_stock_and_pricing, list_vendors, request_payment, request_purchase_order, list_payment_requests |
| Facilities | `facilities.md` | Looks up lease terms, rent, and due dates, flags rent due soon or overdue, sends payment needs to Accounting, and writes landlord drafts only. | get_today, get_ticket, get_rent_status, get_cash_position, save_draft_message |
| Customer Service | `customer_service.md` | Drafts (never sends) customer messages from confirmed facts only, gives honest timelines, and offers a discount only if Accounting approved it. | get_today, get_ticket, check_stock_and_pricing, list_vendors, list_payment_requests, save_draft_message |

Code layout: `config.py` (model, paths, limits), `models.py` (data types), `agents.py` (the five agents, MCP client, delegation, agent loop), `audit.py` (append-only `output/audit_trail.json`), `run.py` (command-line runner).

## All MCP tools (Problem 5)

The three Problem 3 tools are unchanged. The write tools only touch the working copy `data/campus_customs_new.db`. `payment_requests` and `drafts` are extra tables the server creates in the working copy the first time a write tool runs, so a reset from `campus_customs.db` clears them.

| Tool | Tables it uses | Reads / writes | Who can call it |
|---|---|---|---|
| `get_today` | desk | read | all agents |
| `list_open_tickets` | tickets | read | Boss |
| `list_tickets` | tickets | read | dashboard backend (`GET /tickets`) |
| `get_ticket` | tickets | read | all agents |
| `get_invoice_status` | invoices, vendors, desk | read | Inventory, Accounting |
| `get_rent_status` | leases, desk, cash_accounts | read | Accounting, Facilities |
| `check_stock_and_pricing` | inventory, pricing | read | Inventory, Accounting, Customer Service |
| `list_vendors` | vendors, invoices, desk | read | Inventory, Accounting, Customer Service |
| `list_open_invoices` | invoices, vendors, desk | read | Accounting |
| `get_cash_position` | cash_accounts, payment_requests | read | Boss, Accounting, Facilities |
| `request_payment` | invoices or leases, cash_accounts → payment_requests | writes a **pending** request; no money moves | Accounting |
| `request_purchase_order` | vendors, inventory, pricing, invoices, cash_accounts → payment_requests | writes a **pending** request; amount = qty × unit_cost | Accounting |
| `list_payment_requests` | payment_requests | read | Boss, Accounting, Customer Service |
| `save_draft_message` | drafts | writes a draft; never sent | Facilities, Customer Service |
| `update_ticket_status` | tickets | writes status only | Boss |

That is all 15 MCP tools. None of them can move money.

**Human-only actions (not MCP tools).** Two plain functions sit in `mcp_server/server.py` with no `@mcp.tool`, so no MCP client can list or call them: not any agent, and not the IDE's MCP client through `.mcp.json`. Only the human approval path calls them (the dashboard's approve/reject buttons, in a later problem).

| Function | Tables it uses | What it does |
|---|---|---|
| `approve_and_pay(request_id, approved_by)` | payment_requests, cash_accounts, payments, invoices, leases, vendors, desk | **Moves money** after a named human approves. |
| `reject_payment_request(request_id, decided_by, note)` | payment_requests | Records a human's rejection. No money moves. |

`approve_and_pay` refuses in four cases: the request isn't pending, the approver is blank or an agent name, the vendor on a purchase order still has an open invoice, or the payment would make the balance negative. On success it adds a `payments` row, lowers `cash_accounts.balance`, and either marks the invoice `paid` or moves `leases.next_due` forward one month.

## Safety and guardrails

What a real business would want when agents touch real customers and real money:

- **A human approves every payment.** Agents can only create pending requests. Paying is not an MCP tool at all, so no agent or other MCP client can reach it, even by passing a human's name. The backend adds two more checks: it refuses to build an agent whose prompt lists a pay action, and it refuses to start a run if the MCP server ever exposes one. The pay function itself rejects agent names as approvers and requires a named person.
- **No negative balances.** The pay function checks the balance inside a database transaction. Request tools refuse any amount larger than the balance and warn when pending requests together exceed cash.
- **Amounts come from the database, not the model.** Invoice amounts, rent, and PO costs (qty × unit_cost) are looked up by the tool, so an agent can't make up a number.
- **No outbound contact.** Customer and landlord messages are saved as drafts on the board; nothing is emailed or sent to vendors.
- **Least privilege.** Each agent sees only the tools its role needs, and only the human-facing tools change money.
- **Audit everything.** Every agent-loop step is appended to `output/audit_trail.json`: timestamp, run ID, ticket, agent, depth, what it did, each tool call with inputs and result, delegations (from → to), and tokens used. Earlier runs are never overwritten.
- **Resettable data.** Agents only use the working copy; the original database is never opened by the server.
- **One model name in the repo.** The Portkey provider label in the error messages (in `AI_prompts.md` and `output/audit_trail.json`) was shortened to `gpt-6-luna`.
- **Shop calendar everywhere.** Payment requests, decisions, drafts, and payments are all stamped with `desk.date_today`, never the real clock.
- **No false "resolved".** `get_ticket` lists each ticket's `required_payments`: a linked open invoice needs an invoice request, and a linked lease needs a rent request. `update_ticket_status` refuses `resolved` until each one has a pending (or paid) request, for the Boss and for the backend's run route alike. Purchase orders are a judgment call and never required.
- **No re-asking for known facts.** Each run keeps a shared facts board (the preloaded ticket and date, every MCP result, every teammate's answer) shown to every agent on every step. Identical read-only MCP calls in a run come from a cache, which is cleared after any write. A repeat delegation (same asker → same teammate) gets the earlier answer back instead of a new run. No agent can be asked more than twice per run (`MAX_ASKS_PER_AGENT`), and nobody can delegate back to a teammate who is waiting on them.

Limits that keep runs and token use in check (all in `backend/config.py`):

| Limit | Value | What happens when it's hit |
|---|---|---|
| `MAX_DELEGATION_DEPTH` | 3 | Further `delegate` calls are refused and logged; the agent finishes with what it has. |
| `MAX_DELEGATIONS_PER_RUN` | 8 | Same refusal, counted across all agents on the ticket. |
| `MAX_STEPS_PER_RUN` | 30 model requests | The run stops with `limit_reached` in the audit trail. |
| `MAX_TOKENS_PER_RUN` | 150,000 tokens | The run stops with `limit_reached`. |
| `MAX_TOOL_RESULT_CHARS` | 4,000 | Longer tool results are cut short in the audit trail. |
| `MAX_ASKS_PER_AGENT` | 2 | A third request to the same agent in one run gets its earlier answers back instead of a new sub-run. |
| `MAX_FACTS_CHARS` | 8,000 | Caps the shared facts board shown to agents (oldest facts dropped first). |

Step and token limits are shared across every agent working on one ticket, not counted per agent. Agents also can't delegate to themselves.

## Backend routes (Problem 7)

`backend/main.py` (FastAPI). Start it from `backend/` with `uvicorn main:app --reload --port 8000`. CORS allows any `localhost` or `127.0.0.1` origin.

- `GET /` — health check.
- `GET /tickets` — every ticket with its status and `state` (open or resolved), read through the `list_tickets` MCP tool.
- `POST /tickets/{ticket_id}/run` — runs the agent team on one ticket (Boss first). It marks the ticket resolved only when the run finishes and every required payment has a pending request; otherwise the ticket stays open and the response includes `unresolved_reason`. Payments stay pending for a human. Returns the run ID and the Boss summary; calls the model through Portkey.
- `GET /events?limit=50&ticket_id=&run_id=` — recent entries from `output/audit_trail.json`: what each agent said (`said`), the tools it used (`tools_used`), delegations, and tokens.
- `GET /payments?status=pending` — the payment requests the agents prepared (pending, paid, rejected, or all), each with its `payee` (vendor or landlord, looked up through MCP), so the dashboard knows what to approve.
- `POST /payments/{request_id}/approve` (body `{"approved_by": "<name>"}`) — a human approves one pending request; this is the only route that moves money. It calls the human-only `approve_and_pay`, refuses if cash would go negative, and updates payments, cash_accounts, and the linked invoice or lease.
- `GET /cash` — the current checking balance from cash_accounts, plus the total of pending requests.
- `POST /reset` — copies `data/campus_customs.db` over `data/campus_customs_new.db` for a fresh run; the original is only read.

## Dashboard (Problem 8)

`frontend/` (React + Vite + TypeScript). Start it from `frontend/` with `npm run dev`; it opens http://localhost:5173 and calls the backend at http://localhost:8000 (`src/api.ts`). Design choices are in `output/design.md`.

| Area | What it shows | Routes it uses |
|---|---|---|
| Ticket spike (left) | The three tickets as paper stubs, with open/resolved state, a RESOLVED stamp, and how many payments wait on approval | `GET /tickets`, `GET /payments` |
| Crew stage (center) | The five agents as HTML/CSS critters; whoever is working glows and "talks", others show waiting / took part / not needed | `GET /events` |
| Live floor (center) | The run transcript: what each agent said, hand-offs (from → to), and each tool call with its input and result; refreshes every 2.5 s while a run is going | `POST /tickets/{id}/run`, `GET /events` |
| Shift handover (center) | The Boss's summary: the call, what each agent did, what's waiting on a human, draft IDs, tokens used | run result / `run_finished` event |
| Cash drawer (right) | Checking balance, which ticks down when a payment is approved, plus pending total and what would be left | `GET /cash` |
| Approval slips (right) | Each pending request: who it's for, amount, why, who prepared it; Approve & pay; a red REFUSED stamp with the backend's reason; a paid receipt tape | `GET /payments`, `POST /payments/{id}/approve` |
| Reset the day (top) | Two-click reset of the working database | `POST /reset` |

Safety rules the dashboard enforces on top of the backend:

- Approve buttons stay locked until a human types their name in **Signing as**, so every payment carries a named approver.
- Refusals (not enough cash, vendor blocked, agent named as approver) are shown on the slip with the exact reason; nothing is retried automatically.
- A resolved ticket can't be started again until the day is reset, so a second run can't create duplicate payment requests.
- Reset needs a second click and is disabled while a run is going; the backend also refuses to reset or start a second run during a run.
- The dashboard never calls the model directly and has no model name in it; only the backend's run route does.
