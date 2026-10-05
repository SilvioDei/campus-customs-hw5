import { AGENT_ORDER, PERSONAS } from "../agents";
import type { RunView } from "../runlog";
import { Critter } from "./Critter";

// The five agents sit along the top of the desk. Whoever holds the floor
// stands up, glows, and "talks"; agents who weren't needed stay dim.
export function CrewStage({ run, running }: { run: RunView | null; running: boolean }) {
  return (
    <section className="crew" aria-label="Agent crew">
      {AGENT_ORDER.map((name) => {
        const p = PERSONAS[name];
        const speaking = running && run?.speaking === name;
        const involved = run?.involved.has(name) ?? false;
        const line = run?.lastLine[name];
        let status = "off shift";
        if (speaking) status = "speaking";
        else if (running && involved) status = "waiting";
        else if (run && involved) status = "took part";
        else if (run) status = "not needed";
        return (
          <div
            key={name}
            className={`seat seat--${name}${speaking ? " is-speaking" : ""}${run && !involved ? " is-benched" : ""}`}
          >
            <div className="bubble" title={line ?? p.idleLine}>
              {speaking && !line ? <span className="typing"><i /><i /><i /></span> : line ?? p.idleLine}
            </div>
            <Critter agent={name} active={speaking} />
            <div className="seat__name">{p.label}</div>
            <div className="seat__role">{p.role}</div>
            <div className={`seat__status status--${status.replace(" ", "-")}`}>{status}</div>
          </div>
        );
      })}
    </section>
  );
}
