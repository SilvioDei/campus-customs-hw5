import { PERSONAS } from "../agents";
import type { AgentName } from "../types";

// A small desk critter built from HTML/CSS: a round body, ears, blinking eyes,
// a mouth that "talks" while the agent is working, and a role-specific hat.
export function Critter({ agent, active = false, size = 64 }: { agent: AgentName; active?: boolean; size?: number }) {
  const hat = PERSONAS[agent].hat;
  return (
    <div
      className={`critter critter--${agent}${active ? " is-active" : ""}`}
      style={{ ["--s" as string]: `${size}px` }}
      aria-hidden="true"
    >
      <span className={`critter__hat hat--${hat}`} />
      <span className="critter__ear critter__ear--l" />
      <span className="critter__ear critter__ear--r" />
      <span className="critter__body">
        <span className="critter__eye critter__eye--l" />
        <span className="critter__eye critter__eye--r" />
        <span className="critter__cheek critter__cheek--l" />
        <span className="critter__cheek critter__cheek--r" />
        <span className="critter__mouth" />
      </span>
    </div>
  );
}
