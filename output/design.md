# Campus Customs Night Desk: dashboard design

The dashboard (`frontend/`, React + Vite + TypeScript) is meant to feel like a real shop counter after closing time: neon sign on, paper tickets on a spike, a cash register glowing in the corner, and a small crew of agents working the floor. It keeps the black-and-pink palette from `output/desk_tickets.html` (same `--bg`, `--panel`, `--pink`, and `--pink-soft` values) so the plan page and the live desk look like one product.

## Layout: three zones, read left to right

| Zone | What's there | Why |
|---|---|---|
| **Left: the ticket spike** | The three tickets as paper stubs with a perforated tear-off edge, a big monospace ticket number, requester, and SKU/lease. Chips show *open*, *resolved*, *crew working*, and *N to approve*. | Tickets are the work queue, so they sit where you start reading. The paper look makes the queue feel physical. You "pull" a ticket off the spike to work it. |
| **Center: the floor** | The selected ticket's brief and a big pink **Start the crew** button, then the **crew stage** (five agents), the **shift handover** (summary), and the **live floor** (transcript). | The middle is where the action is. You watch the agents work there, the same way you'd watch staff at a counter. |
| **Right: the register** | The **cash drawer** display and the **Needs your signature** tray of approval slips, with the paid receipt tape under them. | Money stays apart from the agents' chatter and always in view. The human's job (signing) sits right next to the cash it affects. |

The top bar holds the neon **Campus Customs** sign, a backend status light, open/resolved counts, the shop day (`desk.date_today`), and **Reset the day**. The zones scroll independently, so the cash drawer never scrolls away while you read a long transcript. Under 1100px wide the zones stack.

## How the agents read differently

Each agent is a little desk **critter built only in HTML/CSS** (no images): a round body, ears, blinking eyes, rosy cheeks, and a hat for its job:

| Agent | Hue | Hat | Voice on the page |
|---|---|---|---|
| Boss | hot pink | gold crown | Bolder, slightly larger text. The Boss has the final say, so its lines carry weight. |
| Inventory | magenta | cardboard box | Monospace, like a stock printout or barcode label. |
| Accounting | rose | green visor | Tabular numbers on faint ledger lines, so figures line up like a ledger. |
| Facilities | lilac | yellow hard hat | Dashed border and a blueprint tint. |
| Customer Service | blush | headset | Italic, with a softer speech-bubble shape. It's the warm, people-facing voice. |

Agents differ by **shape, hat, and typeface, not only color**, so they stay easy to tell apart for color-blind users and in screenshots.

**Live behavior while a run is going:**
- The feed polls `GET /events` every 2.5 s.
- The agent who currently holds the floor **stands up**: it hops, glows, its mouth moves, and its speech bubble shows its latest line. The "speaker" comes from the delegation stack in the audit trail (Boss → Inventory → Accounting…).
- Agents waiting on a teammate say *waiting*. Agents never pulled in fade to grey and say *not needed*, so you can see at a glance that Boss didn't call everyone, which is what the Problem 6 plans predicted.
- In the transcript, a **hand-off** shows as a pink pill (`Boss → Inventory "check stock…"`) and a **hand-back** as a dashed pill. Work done inside a delegation is indented by depth, so the chain of who asked whom reads like a conversation.
- Each tool call is a small chip (`⚙ check_stock_and_pricing`). Click it to see the exact input and result. That's the audit trail, readable.
- A typing indicator at the bottom says the crew is still working and the page is refreshing.

## How resolved tickets show up

- When a run finishes, the backend marks the ticket **resolved**. A green rubber **RESOLVED** stamp slams onto the stub (a scale-in animation), the stub dims slightly, and the ticket number turns grey. The board then shows at a glance what's done.
- The **Shift handover** card appears above the transcript: the Boss's call, one line per agent on what it did, a pink **Waiting on a human** box for anything that needs approval (with amounts and request IDs), and any draft IDs saved on the board (never sent). Token and tool-call counts sit in the corner so cost stays visible.
- A run that hits a safety limit shows a red **Run stopped early** card instead, and the ticket stays open.
- A resolved ticket's start button reads **Resolved · reset to run again**, so nobody re-runs a ticket by accident and creates duplicate payment requests.

## How cash shows up

- The **cash drawer** is a glowing register display (pink seven-segment-style digits with scanlines) showing the checking balance from `GET /cash`.
- When a human approves a payment, the balance **ticks down** and the amount (e.g. `−$840.00`) **falls out** of the display in red, so you see the money leave the drawer.
- Under the display: **Waiting on approval**, **Left if all approved**, and the shop day. If the pending requests add up to more than the cash on hand, the display pulses red and says *"Not everything waiting can be paid. Someone has to choose."* That is the ticket 101/102/103 conflict ($840 + $2,400 + $264 > $3,400), made visible.
- **Approval slips** are pink paper slips with a torn top edge, tilted slightly as if dropped on the desk. Each shows what it is (vendor invoice, rent, purchase order), **who it's for** (vendor or landlord, looked up through MCP), the **amount**, the ref (invoice/lease or `12 × CC-HOOD-NAVY (M)`), **why** (the agent's reason), and who prepared it.
- The approver types their name once in **Signing as** (in a serif italic, so it reads like a signature). Approve buttons stay locked until a name is there, so every payment has a named human.
- If the backend refuses (not enough cash, vendor blocked by an open invoice, an agent name as approver), the slip gets a red outline and a **REFUSED** stamp with the backend's exact reason. The money stays put.
- Paid items print onto a **receipt tape** under the slips, each with the signer's name. It's a running record of what left the drawer today.

## Small touches that make it pleasant to sit at

- The neon sign flickers every few seconds, and the desk surface has a faint graph-paper grid under a pink glow.
- A toast at the bottom confirms each action ("Paid $840.00. Signed by …", "Fresh day…"). Errors are red and stay readable.
- **Reset the day** asks for a second click ("Click again to reset") so it can't be hit by accident. It is disabled while a run is going.
- The signer name is remembered between visits. If the page is reloaded mid-run, the board notices the unfinished run in the audit trail and keeps refreshing.
- A reply for a ticket you've already clicked away from is ignored, so a slow response can't paint the wrong ticket's transcript.
- `prefers-reduced-motion` turns off all animation for people who want a calm screen.

## Why these choices

The desk has two audiences at once: the person watching **what the agents are doing**, and the person responsible for **the money**. The layout keeps them apart (floor in the middle, register on the right) but always both on screen. Personality (the critters, the stamp, the falling cash) makes a long agent run fun to watch. The serious parts stay plain and explicit: amounts, payees, reasons, refusals, and a named signature, because a real business needs to trust what it approves.
