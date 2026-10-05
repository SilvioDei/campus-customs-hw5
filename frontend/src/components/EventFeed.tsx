import { useEffect, useRef } from "react";
import { PERSONAS, timeOf } from "../agents";
import type { AgentEvent } from "../types";
import { Critter } from "./Critter";

function pretty(value: unknown): string {
  if (typeof value === "string") {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }
  return JSON.stringify(value, null, 2);
}

function ToolChip({ call }: { call: AgentEvent["tool_calls"][number] }) {
  if (call.tool === "final_result") return null;
  const isDelegate = call.tool === "delegate";
  return (
    <details className={`tool${isDelegate ? " tool--delegate" : ""}`}>
      <summary>
        <span className="tool__icon">{isDelegate ? "↪" : "⚙"}</span>
        {call.tool}
      </summary>
      <div className="tool__io">
        <div>
          <b>input</b>
          <pre>{pretty(call.args)}</pre>
        </div>
        <div>
          <b>result</b>
          <pre>{pretty(call.result)}</pre>
        </div>
      </div>
    </details>
  );
}

function Line({ e }: { e: AgentEvent }) {
  const p = PERSONAS[e.agent];
  if (e.action === "run_started" || e.action === "run_finished") {
    return (
      <li className="feed__marker">
        <span>{e.action === "run_started" ? "Shift starts · Boss picks up the ticket" : "Boss closes the ticket"}</span>
        <time>{timeOf(e.timestamp)}</time>
      </li>
    );
  }
  if (e.action === "limit_reached" || e.action === "error") {
    return (
      <li className="feed__alarm">
        <b>{e.action === "limit_reached" ? "Safety limit reached" : "Run error"}</b> {e.summary}
      </li>
    );
  }
  if (e.delegation && e.action !== "delegation_finished") {
    const d = e.delegation;
    return (
      <li className={`feed__handoff${e.action === "delegation_refused" ? " is-refused" : ""}`}>
        <span className={`who who--${d.from_agent}`}>{PERSONAS[d.from_agent].label}</span>
        <span className="arrow">{e.action === "delegation_refused" ? "✕" : "→"}</span>
        <span className={`who who--${d.to_agent}`}>{PERSONAS[d.to_agent].label}</span>
        <q>{e.action === "delegation_refused" ? `refused: ${e.summary}` : d.task}</q>
        <time>{timeOf(e.timestamp)}</time>
      </li>
    );
  }
  if (e.action === "delegation_finished" && e.delegation) {
    const d = e.delegation;
    return (
      <li className="feed__handback">
        <span className={`who who--${d.to_agent}`}>{PERSONAS[d.to_agent].label}</span>
        <span className="arrow">↩</span>
        <span className={`who who--${d.from_agent}`}>{PERSONAS[d.from_agent].label}</span>
        <span className="muted">handed the answer back</span>
        <time>{timeOf(e.timestamp)}</time>
      </li>
    );
  }
  const spoke = e.said && !e.said.startsWith("Called ");
  return (
    <li className={`feed__line voice--${e.agent}`} style={{ marginLeft: `${Math.min(e.depth, 3) * 18}px` }}>
      <Critter agent={e.agent} size={30} />
      <div className="feed__body">
        <header>
          <span className={`who who--${e.agent}`}>{p.label}</span>
          <time>{timeOf(e.timestamp)}</time>
          {e.tokens.total_tokens > 0 && <span className="tokens">{e.tokens.total_tokens.toLocaleString()} tok</span>}
        </header>
        {spoke ? <p className="said">{e.said}</p> : <p className="said said--quiet">used tools</p>}
        {e.tool_calls.length > 0 && (
          <div className="tools">
            {e.tool_calls.map((c, i) => (
              <ToolChip key={i} call={c} />
            ))}
          </div>
        )}
      </div>
    </li>
  );
}

// The live transcript of a run, newest at the bottom, auto-scrolling while it runs.
export function EventFeed({ events, running }: { events: AgentEvent[]; running: boolean }) {
  const end = useRef<HTMLLIElement>(null);
  useEffect(() => {
    if (running) end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [events.length, running]);

  if (events.length === 0) {
    return (
      <div className="feed feed--empty">
        <p>No one has worked this ticket yet.</p>
        <p className="muted">Start the crew and their conversation will stream in here.</p>
      </div>
    );
  }
  return (
    <ol className="feed" aria-live="polite">
      {events.map((e) => (
        <Line key={`${e.run_id}-${e.step}`} e={e} />
      ))}
      {running && (
        <li className="feed__pulse" ref={end}>
          <span className="typing"><i /><i /><i /></span> crew is still working · refreshing every few seconds
        </li>
      )}
    </ol>
  );
}
