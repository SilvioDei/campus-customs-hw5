"""Data types for the Campus Customs agent team."""

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
AGENT_NAMES: tuple[AgentName, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")


# ---- Run state shared by every agent working on one ticket ----

@dataclass
class RunState:
    """One ticket run. Shared by all agents so limits apply to the whole run."""

    run_id: str
    ticket_id: int | None
    step: int = 0               # audit sequence number across all agents
    delegations: int = 0        # delegate() calls made so far in this run
    # Shared memory so agents don't re-ask for facts already reported in this run:
    facts: dict[str, str] = field(default_factory=dict)            # key -> one-line fact shown to every agent
    tool_cache: dict[str, Any] = field(default_factory=dict)       # read-only MCP results by (tool, args)
    answers: dict[tuple[str, str], str] = field(default_factory=dict)  # (from, to) -> delegation answer
    asks: dict[str, int] = field(default_factory=dict)             # how many times each agent was delegated to


@dataclass
class AgentDeps:
    """Per-agent dependencies passed to each PydanticAI run."""

    state: RunState
    agent: AgentName
    depth: int = 0                                   # 0 = Boss at the top of the run
    chain: list[AgentName] = field(default_factory=list)  # who delegated to whom, top first


# ---- Audit trail ----

class ToolCallRecord(BaseModel):
    tool: str
    args: Any = None
    result: Any = None


class DelegationRecord(BaseModel):
    from_agent: AgentName
    to_agent: AgentName
    task: str
    depth: int


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class AuditEntry(BaseModel):
    """One agent-loop step (or delegation event) in output/audit_trail.json."""

    timestamp: str
    run_id: str
    step: int
    ticket_id: int | None
    agent: AgentName
    depth: int
    action: Literal[
        "run_started", "model_step", "delegation_started", "delegation_finished",
        "delegation_refused", "run_finished", "limit_reached", "error",
    ]
    summary: str = ""
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    delegation: DelegationRecord | None = None
    tokens: TokenUsage = Field(default_factory=TokenUsage)


# ---- API request bodies ----

class ApprovePaymentBody(BaseModel):
    approved_by: str = Field(min_length=1, description="Name of the human who clicked approve")


# ---- Boss output ----

class Assignment(BaseModel):
    agent: AgentName
    did: str = Field(description="What this agent did or found, using only tool results")


class HumanApproval(BaseModel):
    item: str = Field(description="What needs a human decision, e.g. a pending payment request")
    amount: float | None = Field(default=None, description="Dollar amount from the tools, if money is involved")
    payment_request_id: int | None = Field(default=None, description="ID from request_payment / request_purchase_order")


class TicketSummary(BaseModel):
    """The Boss's final summary for a ticket."""

    ticket_id: int
    decision: str = Field(description="What was decided, including the final call on any competing needs")
    assignments: list[Assignment] = Field(description="Who did what")
    waiting_on_human: list[HumanApproval] = Field(description="Anything that needs human approval")
    draft_ids: list[int] = Field(default_factory=list, description="IDs of drafts saved on the board")
    ticket_status: Literal["open", "in_progress", "waiting_on_human", "resolved"]
