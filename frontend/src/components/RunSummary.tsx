import { PERSONAS, money } from "../agents";
import type { RunView } from "../runlog";
import type { TicketSummary } from "../types";
import { Critter } from "./Critter";

// The Boss's wrap-up, laid out like a shift-handover note.
export function RunSummary({ summary, run, stale }: { summary: TicketSummary | null; run: RunView | null; stale: boolean }) {
  if (!run) return null;
  if (!run.finished) return null;
  if (run.failed) {
    return (
      <section className="summary summary--failed">
        <h3>Run stopped early</h3>
        <p>{run.failed}</p>
        <p className="muted">The ticket stays open. Reset and try again.</p>
      </section>
    );
  }
  if (!summary) {
    return (
      <section className="summary">
        <h3>Shift handover</h3>
        <p className="muted">The run finished, but its summary was too long to keep in the audit trail.</p>
      </section>
    );
  }
  return (
    <section className={`summary${stale ? " is-stale" : ""}`}>
      <header>
        <h3>Shift handover · ticket #{summary.ticket_id}</h3>
        {stale && <span className="chip">from before the last reset</span>}
        <span className="summary__meta">
          {run.toolCount} tool calls · {run.tokens.toLocaleString()} tokens
        </span>
      </header>
      <p className="summary__decision">
        <b>Boss's call:</b> {summary.decision}
      </p>
      <ul className="summary__who">
        {summary.assignments.map((a, i) => (
          <li key={i} className={`voice--${a.agent}`}>
            <Critter agent={a.agent} size={26} />
            <span className={`who who--${a.agent}`}>{PERSONAS[a.agent]?.label ?? a.agent}</span>
            <span>{a.did}</span>
          </li>
        ))}
      </ul>
      {summary.waiting_on_human.length > 0 && (
        <div className="summary__waiting">
          <b>Waiting on a human</b>
          <ul>
            {summary.waiting_on_human.map((w, i) => (
              <li key={i}>
                {w.item}
                {w.amount != null && <span className="amt">{money(w.amount)}</span>}
                {w.payment_request_id != null && <span className="chip">request #{w.payment_request_id}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {summary.draft_ids.length > 0 && (
        <p className="muted">Drafts saved on the board (not sent): {summary.draft_ids.map((d) => `#${d}`).join(", ")}</p>
      )}
    </section>
  );
}
