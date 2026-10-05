"""Append-only audit trail at output/audit_trail.json (a JSON list of entries)."""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any

from .config import AUDIT_TRAIL_PATH, MAX_TOOL_RESULT_CHARS
from .models import AgentDeps, AuditEntry, DelegationRecord, TokenUsage, ToolCallRecord

_lock = threading.Lock()


def _read_entries() -> list[dict]:
    if not AUDIT_TRAIL_PATH.exists() or AUDIT_TRAIL_PATH.stat().st_size == 0:
        return []
    with AUDIT_TRAIL_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{AUDIT_TRAIL_PATH} must hold a JSON list; refusing to overwrite it.")
    return data


def append_entry(entry: AuditEntry) -> None:
    """Add one entry to the end of the trail. Earlier runs are kept."""
    with _lock:
        AUDIT_TRAIL_PATH.parent.mkdir(parents=True, exist_ok=True)
        entries = _read_entries()
        entries.append(entry.model_dump(mode="json"))
        tmp = AUDIT_TRAIL_PATH.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
            f.write("\n")
        os.replace(tmp, AUDIT_TRAIL_PATH)


def clip(value: Any) -> Any:
    """Keep large tool results from bloating the trail."""
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    if len(text) <= MAX_TOOL_RESULT_CHARS:
        return value
    return text[:MAX_TOOL_RESULT_CHARS] + f"... [truncated {len(text) - MAX_TOOL_RESULT_CHARS} chars]"


def record(
    deps: AgentDeps,
    action: str,
    summary: str = "",
    tool_calls: list[ToolCallRecord] | None = None,
    delegation: DelegationRecord | None = None,
    tokens: TokenUsage | None = None,
) -> None:
    deps.state.step += 1
    append_entry(AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        run_id=deps.state.run_id,
        step=deps.state.step,
        ticket_id=deps.state.ticket_id,
        agent=deps.agent,
        depth=deps.depth,
        action=action,
        summary=summary,
        tool_calls=tool_calls or [],
        delegation=delegation,
        tokens=tokens or TokenUsage(),
    ))
