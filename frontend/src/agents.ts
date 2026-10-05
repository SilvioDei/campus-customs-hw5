import type { AgentName } from "./types";

// Each agent reads differently: its own hue, hat, typeface, and voice line.
export interface Persona {
  name: AgentName;
  label: string;
  role: string;
  idleLine: string;
  hat: "crown" | "box" | "visor" | "hardhat" | "headset";
}

export const PERSONAS: Record<AgentName, Persona> = {
  boss: { name: "boss", label: "Boss", role: "Routes tickets · makes the call", idleLine: "Who's up next?", hat: "crown" },
  inventory: { name: "inventory", label: "Inventory", role: "Stock · shortfalls · vendors", idleLine: "Counting hoodies…", hat: "box" },
  accounting: { name: "accounting", label: "Accounting", role: "Cash · margins · pending pay", idleLine: "Ledger's balanced.", hat: "visor" },
  facilities: { name: "facilities", label: "Facilities", role: "Lease · rent · the shop space", idleLine: "Lights are on.", hat: "hardhat" },
  customer_service: { name: "customer_service", label: "Customer Service", role: "Drafts replies · never sends", idleLine: "Inbox is quiet.", hat: "headset" },
};

export const AGENT_ORDER: AgentName[] = ["boss", "inventory", "accounting", "facilities", "customer_service"];

export const money = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 });

export const timeOf = (iso: string) =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
