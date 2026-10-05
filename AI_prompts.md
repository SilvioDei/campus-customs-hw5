# AI Prompts Log

## Problem 1: Vibe coder prompts

### Setup / background prompt

```text
Homework 5: Campus Customs Multi-Agent Operations — Scenario and data

Scenario
Campus Customs Multi-Agent Operations is the agentic team that runs the shop. Open tickets land on a board — customer orders, rent, unpaid bills, discount requests, whatever the shop has to handle. I will build three pieces that talk to each other: an MCP server, a FastAPI backend with a multi-agent team, and a React dashboard so a human can watch the agents at work and approve requests.

My agent team has full connectivity — any agent may delegate tasks to any other agent for help. In this assignment I will build these agents:
- Boss — reads each ticket, decides who should work on it, and makes final calls
- Inventory — checks stock by SKU and size, spots shortfalls, and figures out which vendor can restock
- Accounting — watches cash and invoices, checks margins, and prepares payments or purchase orders for human approval
- Facilities — handles the shop space side (leases, rent, etc.)
- Customer Service — drafts messages for customers

Data
I have downloaded data.zip into my HW 5 project folder. Unzip it so I have data/campus_customs.db. That file is the original shop database. Tables include desk, tickets, inventory, pricing, vendors, leases, cash_accounts, payments, and invoices.

My tools will update the database as tickets get resolved. Make a copy of the database file called data/campus_customs_new.db, and point the MCP server and backend at that working copy. Keep campus_customs.db untouched so I can reset whenever I want to restart resolving the tickets.

Rules of this shop
- The field desk.date_today is "today" for the shop. Use this date to determine what is overdue.
- Vendor lead times come from the vendors table.
- A vendor will not ship new product while they still have an open unpaid invoice.
- Human approval is required for any payment. If a payment is made, update the relevant tables.
- If there is not enough cash, the pay tool must refuse — no negative balances.
- Cash only goes out in this homework. Revenue is not modeled, so no money comes in.
- Before a full run to resolve the tickets, reset the working copy (campus_customs_new.db) back to the original values from campus_customs.db.
- Do not email customers or call real vendors. Drafts stay on the board.

AI calls
Use my PORTKEY_API_KEY for AI calls. Keep the key in a .env file and never hardcode it. For this assignment, use only gpt-6-luna through Portkey for every agent. Multi-agent chats burn tokens fast, and points will be deducted if any other model shows up in the code or runs, so do not add fallback models or any other model names anywhere, including comments and defaults.

Project setup
- Check AGENTS.md. If it names any model other than gpt-6-luna, change it to gpt-6-luna. Do not write the old model name anywhere else.
- Use the .venv in this folder for Python (create it if it doesn't exist).
- Create a .gitignore that excludes .venv/, .env, data.zip, and node_modules/ (for the dashboard later), because the final submission is a public GitHub repo.

How we'll work
We will work one problem at a time. For now, only do the setup: unzip data.zip, create the working copy, and list the tables in the database so I can confirm they match. Do not start building the MCP server, backend, or dashboard until I send the next problem.
```

### Prompt

```text
Problem 1: Vibe coder prompts
Create AI_prompts.md at the start of the assignment and keep it updated as I work. This file is the log of what I typed to you.
I will describe each problem to you in my own words. I will not paste this whole page or the assignment URL and ask you to do everything for me.
Put one section for each problem. Each section must include:
- The problem number and title
- At least one prompt I typed, in my own words as much as possible
- One follow-up prompt if I needed it (and one sentence on what was lacking after the first)

Copy my prompts word for word. Include my setup/background prompt under Problem 1. Only add a section when I start a new problem. Leave the "what was lacking" sentence for me to write.
```

### Follow-up prompt

_None yet._

**What was lacking after the first prompt:** No follow-up was needed; the first prompt worked.

## Problem 2: Study the Campus Customs database

### Prompt

```text
Problem 2: Study the Campus Customs database
Open data/campus_customs.db and look through every table and its fields. Do not change anything in this original file. Copy the original file to data/campus_customs_new.db — later problems update that working copy. (We already made this copy during setup, so just check that it exists and matches the original.)
Study the three open tickets in the tickets table so you see how they link to other tables.
Start output/harness.md. For each table, list the fields and one short line on why that table matters for the agents.
I will keep growing this harness file in later problems.

Do not call any AI model for this problem. Just read the database directly. When you're done, give me a short summary of the three open tickets and which tables each one touches.
```

### Follow-up prompt

_None yet._

**What was lacking after the first prompt:** No follow-up was needed; the first prompt worked.

## Problem 3: Build the MCP server

### Prompt

```text
Problem 3: Build the MCP server
Write an MCP server in mcp_server/ using FastMCP. It will talk to data/campus_customs_new.db. You do not need to connect or run it in this problem, but make sure the file loads without errors.
Every agent in this homework uses the tools in this MCP server. You will add more tools to it later; for now write three tools you know you will need for the tickets in the database. Keep the names clear. Never invent any data, only use information in the database. Ideally, pick one tool for each ticket (101, 102, and 103). For now, all three tools should only read from the database — no tool should change data or make payments yet.
In output/harness.md, add a section listing each of your three MCP tools (keep the table section from Problem 2). For every tool include: which table it reads, which ticket it helps unlock (101, 102, or 103), and one sentence on why that tool is the right one for that ticket. Vague lines like "reads inventory" score low — tie the tool to the ticket.
Also add a short mcp_server/README.md file that explains what the MCP server is for, which database file it uses, and the three tools it has.

Install FastMCP in my .venv and add it to requirements.txt. Do not call any AI model for this problem.
```

### Follow-up prompt

_None yet._

**What was lacking after the first prompt:** No follow-up was needed; the first prompt worked.

## Problem 4: Add the MCP server to vibe coder and test each tool

### Prompt

```text
Problem 4: Add the MCP server to vibe coder and test each tool
In Claude Code, add my MCP server to this project so you can call the tools. Save the connection JSON text in .mcp.json at the project root.
Use the Python inside my .venv to run the server, and use relative paths (not my full C:\Users\... path), since this repo will be public. Tell me what I need to do to restart and approve the server.
```

### Follow-up prompt

```text
The campus-customs MCP server isn't loading and no approval prompt appeared. Do not test any tools yet. Check why: confirm .mcp.json is valid JSON, that the Python path and server file path in it exist, and try starting the server command manually to see if it shows any error. Tell me what you find and what I should do in the desktop app.
```

```text
Yes, create .claude/settings.local.json to pre-approve campus-customs, and add it to .gitignore.
```

```text
First, confirm that .claude/settings.local.json exists and pre-approves campus-customs.
```

```text
I'm continuing HW 5 from another session. Before anything else, read AGENTS.md, AI_prompts.md, and output/harness.md to catch up on the scenario, rules, and what's done so far. Key rules: use only gpt-6-luna through Portkey (no other model names anywhere), never change data/campus_customs.db, and keep logging every prompt I send in AI_prompts.md under the problem we're on, word for word. We are on Problem 4.

With you connected to my MCP server, test each of my three MCP tools. Call them through the MCP connection, not by running the Python file or querying the database directly. Save the evidence in output/mcp_smoke.json. For every tool include:
-    the prompt I asked you
-    the tool name
-    the tool output (must match values in data/campus_customs_new.db)
After testing, check each output against the database directly and tell me if anything doesn't match. Do not call any AI model through Portkey for this problem.
```

**What was lacking after the first prompt:** The first attempt didn't load the MCP server because the chat started in the course folder, not HW 5, so I had to pre-approve the server and start a new session there.

## Problem 5: Build the agentic team

### Prompt

```text
Problem 5: Build the agentic team
Build the agentic team for Campus Customs using PydanticAI: Boss, Inventory, Accounting, Facilities, and Customer Service. Include prompts, models, and agent loops so they can delegate work to each other with full connectivity.
Put the agent prompts in backend/prompts/ — one file per agent. Put data types in backend/models.py, and the agent files under backend/ (the file layout can vary as long as the five roles are clear). Use my PORTKEY_API_KEY and only gpt-6-luna for every agent. Keep the model name in one place in the code.

Here are my prompts for each agent, in my own words. Save each one in its own file in backend/prompts/. Keep my wording; you may add a short "Tools" line at the end of each file listing the exact MCP tools that agent should use.

Boss: You are the Boss of Campus Customs. I want you to read each ticket and choose which agent you think should work on it. I also want you to flag anything that may involve money that a human has to approve. Thirdly, I want you to make the final call when there are competing needs. Lastly, I want you to end with a short summary that shows what was decided, who did what, and what's waiting on a human. Never invent data; only use what the MCP tools return. Use desk.date_today as "today."

Inventory: You are the Inventory agent for Campus Customs. I want you to report all shortfalls: needed, on hand, and the gap. I want you to check stock by SKU and size with the MCP tools; please do not guess. Thirdly, I want you to find the restock vendor and its lead time from the vendors table. Lastly, check for an open unpaid invoice, because that blocks the vendor. If so, send it to Accounting. Never invent data; only use what the MCP tools return. Use desk.date_today as "today."

Accounting: You are the Accounting agent for Campus Customs. I want you to prepare payments and purchase orders as pending requests only, because a human has to approve them. I also want you to never let cash go negative; if there is not enough cash, refuse. Thirdly, I want you to check margins before any discount and never sell below cost. Lastly, when cash can't cover everything, rank what should be paid first and explain why. Remember that no money comes in, only out. Never invent data; only use what the MCP tools return. Use desk.date_today as "today."

Facilities: You are the Facilities agent for Campus Customs. I want you to look up lease terms, rent amount, and due dates with the MCP tools. I also want you to flag rent that is due soon or overdue. Thirdly, I want you to send payment needs to Accounting instead of paying them yourself. Lastly, do not contact the landlord; drafts only. Never invent data; only use what the MCP tools return. Use desk.date_today as "today."

Customer Service: You are the Customer Service agent for Campus Customs. I want you to draft messages for customers, but never send them. I also want you to use only confirmed facts from the other agents and the MCP tools; please do not make up dates. Thirdly, I want you to give honest timelines and do not overpromise. Lastly, do not offer a discount unless Accounting approved it. Never invent data; only use what the MCP tools return. Use desk.date_today as "today."

Add any tools the agents need to your MCP server so they can work on the open tickets. Shop facts come from the MCP server over data/campus_customs_new.db — do not invent a second shop-tools layer that bypasses MCP. The agents should connect to the MCP server as MCP clients.
Payment rules for the new tools: no tool may move money without human approval. Until the dashboard exists, a payment tool should only create a pending payment request. The tool that actually pays must refuse if there isn't enough cash (no negative balances) and must update the relevant tables when a payment is made.
Full connectivity: any agent may delegate to any other agent, but add limits so they can't loop forever — a maximum delegation depth and a maximum number of steps per run.
Wire the agents so they append to output/audit_trail.json as they run: for each agent-loop step, record enough to audit later — timestamp, run ID, ticket, agent, what it did, any tool called with its inputs and result, any delegation (from which agent to which), and tokens used. Append to this file — do not wipe it each run.
In output/harness.md, keep the existing sections and add: each agent, and each MCP tool (including ones you add in this problem) along with which table the tool uses. Also add a short safety section: the guardrails a real business would want when agents touch real customers and real money, plus limits that keep token use in check.
Update mcp_server/README.md so the tool list matches what you have now.
Add any new packages to requirements.txt. Do not run the agents or call Portkey yet. When you're done building, tell me what you made and wait for my next prompt.
```

### Follow-up prompt

```text
Can any agent call the tool that actually pays without a human approving first? If yes, fix it so agents can only create pending payment requests. Also list every MCP tool now in the server.
```

**What was lacking after the first prompt:** My first prompt did not make sure the agents could not reach the pay tool, so I had to follow up to make sure only a human approval can move money and agents can only create pending payment requests.

## Problem 6: Plan the three tickets

### Prompt

```text
Problem 6: Plan the three tickets
Before we run the backend, I am writing down what I expect the team to do on each open ticket. Build output/desk_tickets.html — a single page I can double-click to open in a browser (no server and no other files needed) with one tab per ticket (101, 102, and 103). Also add empty Cash and Reflection tabs for later problems (leave them blank or with a short "coming later" note for now).
On each ticket tab, fill an Expected section only, and leave room for an Actual section I will fill after I run the agents.
For each ticket's Expected section, use my plans below word for word. Do not write or change the plans yourself. Each plan covers:
-    Who the Boss should call first, and why
-    All the agent delegations I expect — not "Boss calls everyone"
-    Which MCP tools I expect that run to use

Ticket 101: The Boss should call Inventory first to check stock, since the ticket is about a tee and stock is zero. Inventory uses check_stock_and_pricing to confirm size S is out. Then Inventory should hand it off to Accounting because of the unpaid invoice that blocks the vendor. Accounting uses get_invoice_status to check invoice 501 and prepares the payment as a pending request for human approval. Then Customer Service drafts a message to the customer with an honest timeline. I don't think we need Facilities, because nothing here involves the shop space.

Ticket 102: The Boss should call Facilities first, since the ticket is a rent notice and Facilities handles leases. Facilities uses get_rent_status to check lease 1, the $2,400 rent, and the due date. Then Facilities should hand it off to Accounting because rent is a payment. Accounting checks that there is enough cash and prepares the payment as a pending request for human approval. I don't think we need Inventory or Customer Service, because no stock or customer is involved.

Ticket 103: The Boss should call Inventory first, since the club wants 20 hoodies and only 8 are in stock. Inventory uses check_stock_and_pricing to confirm the 12-hoodie shortfall and the $22 cost. Then Inventory should hand it off to Accounting because the vendor is blocked by the same unpaid invoice as ticket 101, and the discount needs a margin check. Accounting uses get_invoice_status and the pricing from check_stock_and_pricing to set a discount that never goes below cost. Since cash is tight after the invoice and the rent, the Boss makes the final call on whether to restock the 12 hoodies or only sell the 8. Then Customer Service drafts a reply to the Yale AI Club with the discount Accounting approved and an honest timeline. I don't think we need Facilities, because nothing here involves the shop space.

Do not run the agents or call Portkey for this problem.
```

### Follow-up prompt

_None yet._

**What was lacking after the first prompt:** No follow-up was needed; the first prompt worked.

## Problem 7: Backend routes

### Prompt

```text
Problem 7: Backend routes
My React frontend dashboard (the next problem) needs a backend it can call. In backend/main.py, use FastAPI and add routes that do the following:
-    Return the three tickets and whether each is open or resolved
-    Take a ticket id and run my agent team on that ticket
-    Return recent agent events — what each agent said and which tools they used — so the board can refresh (read them from output/audit_trail.json)
-    Approve a payment or purchase after a human clicks approve (agents only prepare the pay; this route is what actually changes cash). It should approve a specific pending payment request, use the human-approval payment path from Problem 5, refuse if there isn't enough cash, and update the relevant tables.
-    Return the current checking balance from cash_accounts
-    Reset the database to the original values when I want to try a fresh run (copy data/campus_customs.db over data/campus_customs_new.db; never change the original)
From the backend/ folder, start the server with:
uvicorn main:app --reload --port 8000
This turns on my backend at http://localhost:8000 so the frontend dashboard can call those routes. Make sure file paths still work when the server is started from the backend/ folder, and allow the React dashboard to call the backend from the browser (CORS for localhost).
In output/harness.md, keep the existing sections and list each route in one line (what URL / what it does).

Add FastAPI and uvicorn to requirements.txt and install them in my .venv. Start the server and test every route except the one that runs the agents. Do not call Portkey for this problem. Tell me the results.
```

### Follow-up prompt

_None yet._

**What was lacking after the first prompt:** No follow-up was needed; the first prompt worked.

## Problem 8: Agent dashboard

### Prompt

```text
Problem 8: Agent dashboard
Build the frontend dashboard in frontend/ with React + Vite + TypeScript. The page should call the routes we built in Problem 7. At minimum the board should:
-    List all three tickets
-    Let me pick one ticket and start the agent team on it
-    Show each agent and what they are saying / doing while the ticket runs (refresh the events every few seconds while a run is going)
-    Mark a ticket resolved when the run finishes
-    Show a short summary of what each agent did on that ticket
-    Let a human approve a pay or purchase when asked (show each pending request with who it's for, the amount, and why, and show a clear message if the approval is refused)
-    Show the checking balance (it should drop after an approved pay)
-    Have a Reset button that calls the reset route, so I can start a fresh run
Make the dashboard look good. Be creative with the layout and feel — this is a real desk people would want to sit at, so put thought into how it looks. Keep the same black-and-pink theme as output/desk_tickets.html.
Tell the front end to talk to my backend at http://localhost:8000. On the backend, allow the Vite page origin (usually http://localhost:5173) so the browser is allowed to call those routes (check this is already set from Problem 7). Start the board with:
npm run dev
This opens the React desk in my browser so I can pick tickets and watch agents.
Write output/design.md with what you chose for the dashboard look (layout, how agents read differently, how resolved tickets and cash show up) and why — including the creative choices that make it feel special and something humans would actually enjoy using.

First check that Node.js is installed on my computer; if it isn't, stop and tell me how to install it. Build and check the dashboard, but do not run the agent team or call Portkey yet. When you're done, tell me exactly how to start the backend and the dashboard.
```

### Follow-up prompt

_None yet._

**What was lacking after the first prompt:** No follow-up was needed; the first prompt worked.

## Problem 9: Resolve the tickets

### Prompt

```text
Problem 9: Resolve the tickets
I reset the working database data/campus_customs_new.db before the full run so I started clean, and the starting checking balance was $[your number]. Then I ran all three tickets (101, 102, 103) myself on the React board until each was resolved, and I approved the payments myself as the human. My screenshots of the board for each resolved ticket are in output/screenshots/ (101.png, 102.png, 103.png). Do not run the tickets again or call Portkey.
Open output/desk_tickets.html from Problem 6. On each ticket tab, fill the Actual section from this run: which agents worked, what they delegated, and which tools they used. Use output/audit_trail.json as the source. Keep my Expected section unchanged so I can compare the two.
On the Cash tab of the same output/desk_tickets.html, itemize the money:
-    Starting checking balance (after the reset)
-    For each ticket: how cash changed when that ticket resolved, and why (which pay / purchase, dollar amount)
-    Ending checking balance — it must match cash_accounts in the working database
Check the cash math against the payments and cash_accounts tables, and tell me if anything doesn't add up. Wrong cash math loses points even if the board shows every ticket resolved. Also save:
-    output/resolved_tickets.json — for each ticket: id, final status, short outcome, what each agent contributed, and any human approvals
-    output/resolved_board.html — a page I can double-click with my screenshot of the React board for each resolved ticket (101, 102, and 103). Build the images into the page so it still works if the screenshots folder moves.
Make sure the real runs are appended in output/audit_trail.json. Finish output/harness.md so it covers tables, MCP tools, the five agents, API routes, the dashboard, and safety rules.
```

### Follow-up prompt

```text
When I ran ticket 102 from the dashboard, the run stopped with this error: "Function tools with reasoning_effort are not supported for gpt-6-luna in /v1/chat/completions. To use function tools, use /v1/responses or set reasoning_effort to 'none'." Fix it while keeping gpt-6-luna through Portkey for every agent. Do not switch to any other model. Try the /v1/responses approach first; if Portkey doesn't support it, set reasoning_effort to 'none'. Test with one small call only, not a full ticket run, and tell me which fix you used. Then tell me if I need to restart the backend.
```

```text
Problem 9: Resolve the tickets
I reset the working database data/campus_customs_new.db before the full run, so I started clean with a checking balance of $3,400. Then I ran all three tickets (101, 102, 103) myself on the React board until each was resolved. I approved two payments myself as the human: $840 for invoice 501 to Bulldog Print Co and $2,400 rent to Elm City Properties. The ending balance on the board is $160. My screenshots of the board for each resolved ticket are in output/screenshots/ (101.png, 102.png, 103.png). Do not run the tickets again or call Portkey.
```

```text
Please take the three board screenshots for me. Open the React board at http://localhost:5173 in your browser, click ticket 101, and save a screenshot of the full board to output/screenshots/101.png. Do the same for 102 (102.png) and 103 (103.png).
Only view the board: do not click Start the crew, Reset the day, or any approve button, and do not call Portkey. Each screenshot should show the ticket marked resolved and the $160 balance.
Then build output/resolved_board.html with the three images inside the page, and check that it opens on its own.
```

**What was lacking after the first prompt:** My first prompt did not test the agents with a real model call, so the first run failed on a reasoning setting, and after fixing it, ticket 102 was resolved without a rent payment request and ticket 103 hit the 30-request limit. I had to ask for fixes, reset the database, and run all three tickets again. I also had to follow up to save the board screenshots.

## Problem 10: Reflection

### Prompt

```text
Problem 10: Reflection
Open output/desk_tickets.html and fill the Reflection tab with my answers below, word for word. Do not write or change the answers yourself. Keep the ticket tabs and the Cash tab unchanged. Do not call Portkey for this problem.

1. How I would evaluate the agents on each ticket

Ticket 101 (Bulldog tee): It was good but cost a lot. Inventory correctly found 0 size S tees, and Accounting rightly found that unpaid invoice 501, which was three days overdue, blocked Bulldog Print Co from restocking. Accounting also created a pending $840 request and did not pay it, because it required a human approval. I think it did well, but it took 28 tool calls and roughly 27,000+ tokens for one tee, partly because the Boss called on Accounting to check the same request two times.

Ticket 102 (Rent due): It looked resolved, but it was not really done. Accounting correctly found that the $2,400 rent for lease 1 is due September 2, two days after the shop date, and that the $3,400 in checking can cover it. However, Accounting said "I did not create a payment request," so there was nothing for me to approve. The board marked the ticket resolved, but the rent cannot actually be paid. It used 10 tool calls and about 12,600 tokens.

Ticket 103 (Bulk hoodie discount): It did not finish. Inventory found only 8 of the 20 size M hoodies in stock, and Customer Service wrote an honest draft for the Yale AI Club that did not quote a discount or promise a restock date. Then the Boss asked Accounting to check invoice 501 again, even though Inventory had already reported it, and the run hit the safety limit of 30 requests. The ticket stayed open. I think the safety limit did its job by stopping the run before it used more tokens.

I also noticed one data mistake: the $840 payment request was dated 2026-10-05, the real date, instead of the shop date, 2026-08-31. The Boss caught and flagged it, which was good.

2. How Actual compared to my Expected plan on each ticket

Ticket 101: This was mostly what I expected. The Boss called Inventory first, then Accounting, and Facilities was not needed. I expected Customer Service to draft a message to Tauhid with an honest timeline, but it was not used. The agents also used tools I did not name in my plan, such as list_payment_requests, get_ticket, get_cash_position, and update_ticket_status.

Ticket 102: This was different from my plan. I expected the Boss to call Facilities first, because Facilities handles leases. Instead, the Boss went straight to Accounting, and Facilities was never used. I also expected Accounting to prepare a pending $2,400 payment, and it did not.

Ticket 103: This was partly what I expected. Inventory found the 12-hoodie shortfall, and Customer Service drafted a careful reply. But I expected the Boss to make the final call on whether to restock the 12 hoodies or only sell the 8, and it never got there because the run stopped at the limit.

What I learned is that the agents do not always take the path I would choose, so I need to compare my plan to the real run instead of assuming they match.

3. What would have been simpler as one agent with tools, and why

Ticket 102 would have been simpler as one agent. It only needed three steps: read lease 1, check the cash, and create one $2,400 pending payment request. Using two agents and 10 tool calls still missed the payment request. One agent with get_rent_status, get_cash_position, and a payment-request tool would have been faster, cheaper, and easier to check. I think the team approach makes more sense for a ticket like 103, where stock, pricing, a blocked vendor, and a customer reply all come together.

4. Three new problems Campus Customs might face that this agent team could solve with the tools I built

First, next month's rent. After the rent is paid, the lease due date moves to October 2. Facilities could flag it early, and Accounting could check whether there will be enough cash to cover it.

Second, deciding what to pay first. If invoice 501 ($840), the rent ($2,400), and the 12-hoodie order ($264) are all waiting at once, that is $3,504 against only $3,400 in checking. Accounting could rank them and explain which one should be paid first and why.

Third, a customer asking about a different item or size. Inventory could check the stock and whether the vendor is blocked, and Customer Service could draft an honest reply without promising dates.

5. Three new problems Campus Customs might face that this agent team could not solve with the tools I built, and the tools and agents I would need

First, tracking sales and money coming in. In this homework, cash only goes out, so the team cannot see whether selling hoodies would help pay the bills. I would add a sales table, a "record sale" tool, and a Sales agent.

Second, actually contacting customers and vendors. Right now the drafts stay on the board, so Tauhid and the Yale AI Club never hear back. I would add an email tool that only sends a message after a human approves it.

Third, planning ahead for busy times, like a hoodie rush before a big game or commencement. There is no sales history or calendar in the database. I would add a sales history table, a forecasting tool, and a Planning agent so the shop can restock before it runs out.
```

### Follow-up prompt

```text
Yes, please fix both: stamp payment requests with desk.date_today, and don't mark a ticket resolved until any payment it needs has a pending request. Also stop agents from re-asking for facts already reported in the same run, so 103 can finish within the limit (raise it a little, to 40, only if still needed). Keep gpt-6-luna for every agent. Do not run the tickets yourself. Tell me if I need to restart the backend.
```

```text
Problem 10 follow-up: Replace the whole Reflection tab in output/desk_tickets.html with my updated answers below, word for word. Do not write or change the answers yourself. Keep the ticket tabs and the Cash tab unchanged. Do not call Portkey.

1. How I would evaluate the agents on each ticket

I ran the tickets twice. The first run showed problems, I asked for fixes, and then I reset the database and ran all three again. My evaluation is mostly about the final run, but I mention the first run where it helped me learn.

Ticket 101 (Bulldog tee): It was good but cost a lot. Inventory correctly found 0 size S tees, and Accounting rightly found that unpaid invoice 501, which was three days overdue, blocked Bulldog Print Co from restocking. Accounting created a pending $840 request and did not pay it, because it required a human approval. I approved it, and checking went from $3,400 to $2,560. In the first run it took 28 tool calls and 27,476 tokens, partly because the Boss asked Accounting to check the same request two times. After the fixes, it took 12 requests and 25,619 tokens, which is better but still a lot for one tee.

Ticket 102 (Rent due): In the first run, the board said resolved, but Accounting said "I did not create a payment request," so the rent could not be paid. After the fix, a ticket cannot be resolved until its payment request exists. In the final run, Accounting created a pending $2,400 rent request, I approved it, and checking went from $2,560 to $160. The lease's next due date then moved to 2026-10-02.

Ticket 103 (Bulk hoodie discount): In the first run, it hit the safety limit of 30 requests because Accounting was asked five times and invoice 501 was checked four times. After the fixes, it finished in only 8 requests. Inventory found that 8 of the 20 size M hoodies are in stock and 12 are short, and that Bulldog Print Co is no longer blocked because invoice 501 was paid. However, Inventory recommended restocking 12 hoodies, which would cost $264, while only $160 was left in checking, and no agent flagged that. I also did not see the discount request get a clear answer.

I also noticed that no customer messages were drafted in the final run, so Tauhid and the Yale AI Club would not hear back yet.

2. How Actual compared to my Expected plan on each ticket

Ticket 101: This was mostly what I expected. Inventory went first, then Accounting, and Facilities was not needed. I expected Customer Service to draft a message to Tauhid with an honest timeline, but it was not used. The agents also used tools I did not name in my plan, such as list_payment_requests, get_ticket, get_cash_position, and update_ticket_status.

Ticket 102: This was different from my plan in both runs. I expected the Boss to call Facilities first, because Facilities handles leases. Instead, the Boss went straight to Accounting, and Facilities was never used. In the final run, Accounting did create the pending $2,400 request that I expected.

Ticket 103: This was partly what I expected. Inventory found the 12-hoodie shortfall. But I expected Accounting to check the margin and set a safe discount, the Boss to decide whether to restock or only sell the 8, and Customer Service to reply to the Yale AI Club. In the final run, none of those steps happened clearly.

What I learned is that the agents do not always take the path I would choose, so I need to compare my plan to the real run instead of assuming they match.

3. What would have been simpler as one agent with tools, and why

Ticket 102 would have been simpler as one agent. It only needed three steps: read lease 1, check the cash, and create one $2,400 pending payment request. In the first run, two agents still missed the payment request. One agent with get_rent_status, get_cash_position, and a payment-request tool would have been faster, cheaper, and easier to check. I think the team approach makes more sense for a ticket like 103, where stock, pricing, cash, and a customer reply all come together, but only if the agents actually talk to each other about cash.

4. Three new problems Campus Customs might face that this agent team could solve with the tools I built

First, next month's rent. The lease is now due October 2. Facilities could flag it early, and Accounting could check whether the $160 left will cover it, which it will not.

Second, deciding what to pay first. If an invoice, rent, and a restock order are all waiting at once, Accounting could rank them and explain which one to pay first, like it would have needed to with $840, $2,400, and $264 against $3,400.

Third, a customer asking about a different item or size. Inventory could check the stock and whether the vendor is blocked, and Customer Service could draft an honest reply without promising dates.

5. Three new problems Campus Customs might face that this agent team could not solve with the tools I built, and the tools and agents I would need

First, tracking sales and money coming in. In this homework, cash only goes out, so after paying the bills the shop has $160 and no way to earn more. I would add a sales table, a "record sale" tool, and a Sales agent.

Second, actually contacting customers and vendors. Right now the drafts stay on the board, so Tauhid and the Yale AI Club never hear back. I would add an email tool that only sends a message after a human approves it.

Third, planning ahead for busy times, like a hoodie rush before a big game or commencement. There is no sales history or calendar in the database. I would add a sales history table, a forecasting tool, and a Planning agent so the shop can restock before it runs out.
```

**What was lacking after the first prompt:** My first reflection was written from the first run, so after I fixed the agents and reran the tickets, I had to update it with the final results.

## Problem 11: Push to GitHub

### Prompt

```text
Problem 11: Push to GitHub
Push my code to a public GitHub repository so graders can clone it. I will submit the repo URL to Canvas; also put it in output/github_url.txt.
Do not push my real .env to the GitHub repo. Instead, add a .env.example with PORTKEY_API_KEY= and no value. Do include both database files under data/ (the original and my working copy) so graders can run my app easily. Expected file layout must conform to what was posted at the beginning of the assignment.
README should explain: copy the original DB to the working copy when you need a clean run, start the MCP server, start the FastAPI backend, start the React board, and reset the DB before a full three-ticket run. Include the Windows commands that worked for me: ..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000 for the backend and npm.cmd run dev for the board, plus pip install -r requirements.txt and npm install for setup.

Before pushing:
- Make sure .gitignore excludes .env, .venv/, node_modules/, data.zip, and .claude/settings.local.json.
- Search every file that will be pushed (including AI_prompts.md and output/audit_trail.json) for my Portkey API key and for any model name other than gpt-6-luna. If you find either, stop and tell me.
- Show me the full list of files that will be committed and wait for my OK.

If git or the GitHub CLI isn't set up on my computer, or I need to log in, stop and tell me step by step what to do. Do not call Portkey for this problem.
```

### Follow-up prompt

```text
1. Replace gpt-6-luna with gpt-6-luna in all 5 places, and add one line to the safety section of output/harness.md saying the Portkey provider label in the error messages was shortened to gpt-6-luna, without writing the full label.
2. Yes, reword your four notes to say "the IDE's MCP client." Keep my prompts word for word.
3. Keep the layout as it is. I will compare it with the assignment post myself.
4. Drop all three from the repo by adding them to .gitignore. Don't delete them from my computer.
5. Yes, use campus-customs-hw5, public, under SilvioDei.
OK, go ahead: make the changes, re-run the scan, commit, create the public repo, push, and write the URL to output/github_url.txt. Then give me the repo link.
```

**What was lacking after the first prompt:** _(to be written)_
