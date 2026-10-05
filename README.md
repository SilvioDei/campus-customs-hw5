# Campus Customs Multi-Agent Operations (HW 5)

An agent team runs a campus merch shop. Open tickets (customer orders, rent, unpaid bills, discount requests) land on a board; five PydanticAI agents (Boss, Inventory, Accounting, Facilities, Customer Service) work them through an MCP server over a SQLite database, and a human approves every payment on a React dashboard.

- **MCP server** (`mcp_server/`, FastMCP): the shop tools over `data/campus_customs_new.db`. No MCP tool can move money.
- **Backend** (`backend/`, FastAPI + PydanticAI): the five agents, with delegation limits and an append-only audit trail, plus the routes the board calls. Every agent uses `gpt-6-luna` through Portkey.
- **Board** (`frontend/`, React + Vite + TypeScript): pick a ticket, watch the agents work, approve payments, see the checking balance.

## Layout

```
HW 5/
├── AI_prompts.md            # every prompt, by problem
├── README.md
├── requirements.txt         # Python packages
├── .env.example             # copy to .env and add your key
├── .mcp.json                # MCP server config (relative paths)
├── data/
│   ├── campus_customs.db        # original shop database (never changed)
│   └── campus_customs_new.db    # working copy the tools update
├── mcp_server/
│   ├── server.py            # FastMCP server and tools
│   └── README.md
├── backend/
│   ├── main.py              # FastAPI routes
│   ├── agents.py            # the five agents, delegation, agent loop
│   ├── models.py            # data types
│   ├── config.py            # model name, paths, limits
│   ├── audit.py             # writes output/audit_trail.json
│   ├── run.py               # command-line runner
│   └── prompts/             # one prompt file per agent
├── frontend/                # React board (src/, package.json, vite.config.ts)
└── output/
    ├── harness.md           # tables, MCP tools, agents, routes, dashboard, safety
    ├── mcp_smoke.json       # MCP tool test evidence
    ├── desk_tickets.html    # Expected vs Actual per ticket, Cash, Reflection
    ├── design.md            # dashboard design choices
    ├── audit_trail.json     # every agent step from the runs
    ├── resolved_tickets.json
    ├── resolved_board.html  # board screenshots, embedded in the page
    ├── screenshots/         # 101.png, 102.png, 103.png
    └── github_url.txt
```

## Setup (Windows, PowerShell)

You need Python 3 and Node.js. Run these from the `HW 5` folder.

1. Create the virtual environment and install the Python packages:

   ```powershell
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   (With the venv activated, `pip install -r requirements.txt` does the same.)

2. Install the board's packages:

   ```powershell
   cd frontend
   npm.cmd install
   cd ..
   ```

3. Add your Portkey key. Copy `.env.example` to `.env` and put your key after `PORTKEY_API_KEY=`. The backend reads `.env` from this folder or its parent folder. Never commit `.env`.

   ```powershell
   Copy-Item .env.example .env
   ```

## Clean database

`data/campus_customs.db` is the original and is never changed. The tools only use the working copy, `data/campus_customs_new.db`. When you need a clean run, copy the original over the working copy:

```powershell
Copy-Item -Force data\campus_customs.db data\campus_customs_new.db
```

## Run it

Use three terminals, all starting in the `HW 5` folder.

**1. MCP server** (optional to start by hand: the backend starts its own copy over stdio when the agents run, and `.mcp.json` lets an MCP client such as an IDE agent connect to it):

```powershell
.venv\Scripts\python.exe mcp_server\server.py
```

**2. FastAPI backend** at http://localhost:8000:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

**3. React board** at http://localhost:5173 (opens in your browser):

```powershell
cd frontend
npm.cmd run dev
```

## Full three-ticket run

1. **Reset the database first.** Click **Reset the day** on the board (it copies the original over the working copy), or run the `Copy-Item` command above while the backend is stopped.
2. Pick ticket 101, 102, or 103 and click **Start the crew**. The agents' steps stream into the board and are appended to `output/audit_trail.json`.
3. When a payment request appears under **Needs your signature**, type your name in **Signing as** and approve it. Only this human approval moves money; it refuses anything that would make checking negative.
4. A ticket shows **resolved** once its run finishes and every payment it needs has a request.

Starting checking is $3,400. In the recorded run, a human approved invoice 501 ($840) and the rent ($2,400), leaving $160. See `output/desk_tickets.html` (Cash tab) and `output/resolved_tickets.json`.

## API routes

| Route | What it does |
|---|---|
| `GET /tickets` | All tickets and whether each is open or resolved |
| `POST /tickets/{id}/run` | Run the agent team on one ticket |
| `GET /events` | Recent agent events from `output/audit_trail.json` |
| `GET /payments` | Payment requests the agents prepared |
| `POST /payments/{id}/approve` | A human approves one pending request; the only route that moves money |
| `GET /cash` | Current checking balance |
| `POST /reset` | Copy the original database over the working copy |

More detail: `output/harness.md`, `mcp_server/README.md`, `output/design.md`.
