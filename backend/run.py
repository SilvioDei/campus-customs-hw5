"""Run the agent team on tickets from the command line.

    .venv/Scripts/python.exe -m backend.run 101        # one ticket
    .venv/Scripts/python.exe -m backend.run --all      # every open ticket

Each run calls the model through Portkey and appends to output/audit_trail.json.
Reset data/campus_customs_new.db from data/campus_customs.db before a full run.
"""

import argparse
import asyncio
import json

from .agents import Team


async def main(ticket_ids: list[int], run_all: bool) -> None:
    team = Team()
    ids = await team.open_ticket_ids() if run_all else ticket_ids
    for ticket_id in ids:
        result = await team.run_ticket(ticket_id)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticket_ids", nargs="*", type=int)
    parser.add_argument("--all", action="store_true", help="work every open ticket")
    args = parser.parse_args()
    if not args.ticket_ids and not args.all:
        parser.error("give ticket IDs or --all")
    asyncio.run(main(args.ticket_ids, args.all))
