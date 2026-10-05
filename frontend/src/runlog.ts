// Turns raw audit-trail events into "what is happening on this ticket".
import type { AgentEvent, AgentName, TicketSummary } from "./types";

export interface RunView {
  runId: string;
  events: AgentEvent[];
  startedAt: string;
  finished: boolean;
  failed: string | null;
  summary: TicketSummary | null;
  speaking: AgentName | null;              // who holds the floor right now
  involved: Set<AgentName>;                // everyone who took part
  lastLine: Partial<Record<AgentName, string>>;
  tokens: number;
  toolCount: number;
  olderRuns: number;
}

const END_ACTIONS = new Set(["run_finished", "limit_reached", "error"]);

export function latestRun(events: AgentEvent[]): RunView | null {
  const starts = events.filter((e) => e.action === "run_started");
  if (starts.length === 0) return null;
  const start = starts[starts.length - 1];
  const run = events.filter((e) => e.run_id === start.run_id).sort((a, b) => a.step - b.step);

  // Delegations nest like a call stack: whoever was handed the work last is speaking.
  const stack: AgentName[] = ["boss"];
  const involved = new Set<AgentName>(["boss"]);
  const lastLine: Partial<Record<AgentName, string>> = {};
  let tokens = 0;
  let toolCount = 0;
  let finished = false;
  let failed: string | null = null;
  let summary: TicketSummary | null = null;

  for (const e of run) {
    tokens += e.tokens?.total_tokens ?? 0;
    if (e.action === "delegation_started" && e.delegation) {
      stack.push(e.delegation.to_agent);
      involved.add(e.delegation.to_agent);
    } else if (e.action === "delegation_finished" && e.delegation) {
      const i = stack.lastIndexOf(e.delegation.to_agent);
      if (i > 0) stack.splice(i, 1);
    } else if (e.action === "model_step") {
      toolCount += e.tool_calls.filter((c) => c.tool !== "final_result").length;
      if (e.said && !e.said.startsWith("Called ")) lastLine[e.agent] = e.said;
    }
    if (END_ACTIONS.has(e.action)) {
      finished = true;
      if (e.action !== "run_finished") failed = e.summary;
      else summary = parseSummary(e.summary);
    }
  }

  return {
    runId: start.run_id,
    events: run,
    startedAt: start.timestamp,
    finished,
    failed,
    summary,
    speaking: finished ? null : stack[stack.length - 1],
    involved,
    lastLine,
    tokens,
    toolCount,
    olderRuns: starts.length - 1,
  };
}

function parseSummary(text: string): TicketSummary | null {
  try {
    return JSON.parse(text) as TicketSummary;
  } catch {
    return null; // truncated in the audit trail; the live run result still has it
  }
}
