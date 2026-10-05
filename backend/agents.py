"""The Campus Customs agent team: Boss, Inventory, Accounting, Facilities, Customer Service.

Every agent is a PydanticAI agent that is an MCP client of mcp_server/server.py.
Each one only sees the MCP tools named on the "Tools:" line of its prompt file,
plus `delegate`, which lets any agent hand work to any other agent (full
connectivity) within the depth, delegation, step, and token limits in config.py.
Every agent-loop step is appended to output/audit_trail.json.

So agents don't re-ask for facts already reported in the same run, each run
keeps a shared facts board (every MCP result and every teammate's answer),
shown to every agent on every step; identical read-only MCP calls are served
from a per-run cache; and repeat delegations reuse the earlier answer.
"""

import json
import re
import sys
import uuid
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent, RunContext, Tool, UsageLimits
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ModelRequest, ModelResponse, RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models import Model

from .audit import clip, record
from .config import (
    MAX_ASKS_PER_AGENT, MAX_DELEGATION_DEPTH, MAX_DELEGATIONS_PER_RUN, MAX_FACT_CHARS, MAX_FACTS_CHARS,
    MAX_STEPS_PER_RUN, MAX_TOKENS_PER_RUN, MCP_SERVER_SCRIPT, PROJECT_DIR, PROMPTS_DIR, get_model,
)
from .models import (
    AGENT_NAMES, AgentDeps, AgentName, DelegationRecord, RunState, TicketSummary, TokenUsage,
    ToolCallRecord,
)

# Actions that move money or decide payments. They are not MCP tools at all (see
# mcp_server/server.py); only the human approval path calls them. These checks
# make sure no agent prompt lists them and the MCP server never exposes them.
HUMAN_ONLY_TOOLS = {"approve_and_pay", "reject_payment_request"}

ROLE_LABELS: dict[AgentName, str] = {
    "boss": "Boss",
    "inventory": "Inventory",
    "accounting": "Accounting",
    "facilities": "Facilities",
    "customer_service": "Customer Service",
}

TEAM_NOTE = f"""
Team: boss, inventory, accounting, facilities, customer_service. Use the `delegate`
tool to ask any teammate for help; say which ticket and exactly what you need back.
Delegation stops at depth {MAX_DELEGATION_DEPTH} and {MAX_DELEGATIONS_PER_RUN} delegations per
ticket, so ask only for what you need. No agent can pay anything; payments wait on a human.
"Facts already confirmed in this run" (below, when present) lists every tool result and
teammate answer so far. Use those facts; do not call a tool again or ask a teammate to
re-check anything already listed, and never delegate back to a teammate who is waiting on you.
"""

# MCP tools that only read. Identical calls in one run are answered from a cache.
READ_ONLY_TOOLS = {
    "get_today", "list_open_tickets", "list_tickets", "get_ticket", "get_invoice_status",
    "get_rent_status", "check_stock_and_pricing", "list_vendors", "list_open_invoices",
    "get_cash_position", "list_payment_requests",
}
# Read results that a write tool (new request, draft, status change) can make stale.
STALE_AFTER_WRITE = {"get_ticket", "list_open_tickets", "list_tickets", "get_cash_position", "list_payment_requests"}


def _key(tool: str, args: dict[str, Any] | None) -> str:
    return f"{tool}({json.dumps(args or {}, sort_keys=True)})"


def _short(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str, separators=(",", ":"))
    return text if len(text) <= MAX_FACT_CHARS else text[:MAX_FACT_CHARS] + "…"


def add_fact(state: RunState, key: str, line: str) -> None:
    state.facts.pop(key, None)  # re-adding moves it to the newest position
    state.facts[key] = line


def render_facts(state: RunState) -> str | None:
    if not state.facts:
        return None
    lines, total = [], 0
    for line in reversed(list(state.facts.values())):  # keep the newest facts if over budget
        if total + len(line) > MAX_FACTS_CHARS:
            break
        lines.append(line)
        total += len(line)
    return "Facts already confirmed in this run (use these; don't re-check them):\n" + "\n".join(reversed(lines))


def load_prompt(name: AgentName) -> tuple[str, set[str]]:
    """Return an agent's prompt text and the MCP tools listed on its Tools line."""
    text = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    match = re.search(r"^Tools:\s*(.+)$", text, flags=re.MULTILINE)
    tools = {t.strip() for t in match.group(1).split(",")} if match else set()
    leaked = tools & HUMAN_ONLY_TOOLS
    if leaked:
        raise ValueError(f"{name}.md lists human-only tools {leaked}; agents may not pay.")
    return text, tools


def build_mcp_toolset(process_tool_call=None) -> MCPToolset:
    """Connect to the Campus Customs MCP server over stdio, as an MCP client."""
    transport = StdioTransport(
        command=sys.executable, args=[str(MCP_SERVER_SCRIPT)], cwd=str(PROJECT_DIR)
    )
    return MCPToolset(Client(transport), process_tool_call=process_tool_call)


def _usage_of(response: ModelResponse) -> TokenUsage:
    u = response.usage
    return TokenUsage(input_tokens=u.input_tokens, output_tokens=u.output_tokens,
                      total_tokens=u.input_tokens + u.output_tokens)


def _tool_results(request: ModelRequest) -> dict[str, Any]:
    results = {}
    for part in request.parts:
        if isinstance(part, ToolReturnPart):
            results[part.tool_call_id] = part.content
        elif isinstance(part, RetryPromptPart) and part.tool_call_id:
            results[part.tool_call_id] = {"retry": part.model_response()}
    return results


def _log_step(deps: AgentDeps, response: ModelResponse, results: dict[str, Any]) -> None:
    calls = [p for p in response.parts if isinstance(p, ToolCallPart)]
    text = " ".join(p.content for p in response.parts if isinstance(p, TextPart)).strip()
    summary = text or (f"Called {', '.join(c.tool_name for c in calls)}" if calls else "No output")
    record(
        deps, "model_step", clip(summary),
        tool_calls=[
            ToolCallRecord(tool=c.tool_name, args=c.args_as_dict(), result=clip(results.get(c.tool_call_id)))
            for c in calls
        ],
        tokens=_usage_of(response),
    )


class Team:
    """The five agents, sharing one MCP connection and one set of run limits."""

    def __init__(self, model: Model | None = None):
        self.mcp = build_mcp_toolset(self._process_tool_call)
        self.model = model or get_model()
        self.agents: dict[AgentName, Agent] = {name: self._build_agent(name) for name in AGENT_NAMES}

    def _build_agent(self, name: AgentName) -> Agent:
        prompt, allowed = load_prompt(name)
        agent = Agent(
            self.model,
            name=name,
            instructions=prompt + TEAM_NOTE,
            deps_type=AgentDeps,
            output_type=TicketSummary if name == "boss" else str,
            toolsets=[self.mcp.filtered(lambda ctx, tool_def, allowed=allowed: tool_def.name in allowed)],
            tools=[Tool(self._delegate, name="delegate")],
            retries=2,
        )

        @agent.instructions
        def facts_so_far(ctx: RunContext[AgentDeps]) -> str | None:
            # Re-evaluated on every model request, so new facts show up mid-run.
            return render_facts(ctx.deps.state)

        return agent

    async def _process_tool_call(self, ctx: RunContext[AgentDeps], call_tool, name: str, args: dict[str, Any]):
        """Every MCP call goes through here: serve repeats from the run's cache and
        post each result to the shared facts board."""
        state = ctx.deps.state
        key = _key(name, args)
        if name in READ_ONLY_TOOLS and key in state.tool_cache:
            return state.tool_cache[key]
        result = await call_tool(name, args)
        if name in READ_ONLY_TOOLS:
            state.tool_cache[key] = result
        else:  # a write can make some earlier reads stale
            for k in [k for k in state.tool_cache if k.split("(")[0] in STALE_AFTER_WRITE]:
                del state.tool_cache[k]
            for k in [k for k in state.facts if k.split("(")[0] in STALE_AFTER_WRITE]:
                del state.facts[k]
        add_fact(state, key, f"- {ctx.deps.agent} ran {key} -> {_short(result)}")
        return result

    async def _delegate(self, ctx: RunContext[AgentDeps], to_agent: AgentName, task: str) -> str:
        """Hand part of the ticket to a teammate and get their answer back.

        Check "Facts already confirmed in this run" first; don't ask for anything
        already listed there.

        Args:
            to_agent: boss, inventory, accounting, facilities, or customer_service.
            task: What you need from them, with the facts they need to do it.
        """
        deps = ctx.deps
        state = deps.state
        pair = (deps.agent, to_agent)
        delegation = DelegationRecord(from_agent=deps.agent, to_agent=to_agent, task=task, depth=deps.depth + 1)

        # Repeat asks reuse what the teammate already said instead of running them again.
        reuse = None
        if pair in state.answers:
            reuse = f"{ROLE_LABELS[to_agent]} already answered you earlier in this run:\n{state.answers[pair]}"
        elif state.asks.get(to_agent, 0) >= MAX_ASKS_PER_AGENT:
            earlier = [a for (f, t), a in state.answers.items() if t == to_agent]
            reuse = (f"{ROLE_LABELS[to_agent]} has already been asked {MAX_ASKS_PER_AGENT} times this run. "
                     "Their earlier answers:\n" + ("\n---\n".join(earlier) or "(still working)"))
        if reuse:
            record(deps, "delegation_refused", "repeat request; reused the earlier answer", delegation=delegation)
            return reuse + "\nUse this and the facts board; finish your part."

        if to_agent == deps.agent:
            refusal = "an agent cannot delegate to itself"
        elif to_agent in deps.chain:
            refusal = f"{ROLE_LABELS[to_agent]} is waiting on you; answer them with what you have instead of asking back"
        elif deps.depth + 1 > MAX_DELEGATION_DEPTH:
            refusal = f"max delegation depth {MAX_DELEGATION_DEPTH} reached"
        elif state.delegations >= MAX_DELEGATIONS_PER_RUN:
            refusal = f"max {MAX_DELEGATIONS_PER_RUN} delegations per run reached"
        else:
            refusal = None
        if refusal:
            record(deps, "delegation_refused", refusal, delegation=delegation)
            return f"Delegation refused: {refusal}. Finish with the facts you already have."

        state.delegations += 1
        state.asks[to_agent] = state.asks.get(to_agent, 0) + 1
        state.answers[pair] = "(still working on it)"  # parallel repeats see this instead of re-running
        record(deps, "delegation_started", f"{deps.agent} -> {to_agent}", delegation=delegation)
        child = AgentDeps(state=state, agent=to_agent, depth=deps.depth + 1,
                          chain=[*deps.chain, deps.agent])
        prompt = (f"Ticket {state.ticket_id}. {ROLE_LABELS[deps.agent]} asks you: {task}\n"
                  f"(Delegation chain so far: {' -> '.join([*child.chain, to_agent])})")
        output = await self.run_agent(to_agent, prompt, child, usage=ctx.usage)
        answer = output if isinstance(output, str) else output.model_dump_json()
        state.answers[pair] = answer
        add_fact(state, f"answer:{to_agent}<-{deps.agent}",
                 f"- {ROLE_LABELS[to_agent]} told {ROLE_LABELS[deps.agent]}: {_short(answer)}")
        record(deps, "delegation_finished", clip(answer), delegation=delegation)
        return answer

    async def run_agent(self, name: AgentName, prompt: str, deps: AgentDeps, usage=None) -> Any:
        """Run one agent's loop, logging every model step with its tool calls and results.

        `usage` is shared with the parent run, so the step and token limits cover
        every agent working on the ticket, not each agent separately.
        """
        limits = UsageLimits(request_limit=MAX_STEPS_PER_RUN, total_tokens_limit=MAX_TOKENS_PER_RUN)
        async with self.agents[name].iter(prompt, deps=deps, usage=usage, usage_limits=limits) as run:
            pending: ModelResponse | None = None
            async for node in run:
                if Agent.is_call_tools_node(node):
                    if pending is not None:
                        _log_step(deps, pending, {})
                    pending = node.model_response
                elif Agent.is_model_request_node(node) and pending is not None:
                    _log_step(deps, pending, _tool_results(node.request))
                    pending = None
            if pending is not None:
                _log_step(deps, pending, {})
            return run.result.output

    async def run_ticket(self, ticket_id: int) -> dict:
        """Boss works one ticket end to end. Returns the run ID and the Boss summary."""
        state = RunState(run_id=uuid.uuid4().hex[:12], ticket_id=ticket_id)
        deps = AgentDeps(state=state, agent="boss")
        record(deps, "run_started", f"Boss picks up ticket {ticket_id}")
        prompt = (f"Work ticket {ticket_id}. The ticket and today's date are already on the facts board. "
                  "Route the work to the right teammates, make sure every payment the ticket needs has a "
                  "pending request (see required_payments), and finish with your summary.")
        try:
            async with self.mcp:
                exposed = {t.name for t in await self.mcp.list_tools()} & HUMAN_ONLY_TOOLS
                if exposed:
                    raise RuntimeError(f"MCP server exposes money-moving tools {exposed}; refusing to run agents.")
                # Preload the facts every agent starts by fetching, so nobody spends a request on them.
                for tool, args in (("get_today", {}), ("get_ticket", {"ticket_id": ticket_id})):
                    result = await self.mcp.direct_call_tool(tool, args)
                    state.tool_cache[_key(tool, args)] = result
                    add_fact(state, _key(tool, args), f"- preloaded {_key(tool, args)} -> {_short(result)}")
                summary: TicketSummary = await self.run_agent("boss", prompt, deps)
        except UsageLimitExceeded as exc:
            record(deps, "limit_reached", str(exc))
            return {"run_id": state.run_id, "ticket_id": ticket_id, "error": f"Limit reached: {exc}"}
        except Exception as exc:
            record(deps, "error", f"{type(exc).__name__}: {exc}")
            raise
        record(deps, "run_finished", clip(summary.model_dump_json()))
        return {"run_id": state.run_id, "ticket_id": ticket_id, "summary": summary.model_dump()}

    async def open_ticket_ids(self) -> list[int]:
        async with self.mcp:
            result = await self.mcp.direct_call_tool("list_open_tickets", {})
        return [t["id"] for t in result["tickets"]]
