// Shapes returned by the FastAPI backend (backend/main.py).

export type AgentName = "boss" | "inventory" | "accounting" | "facilities" | "customer_service";

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku: string | null;
  size: string | null;
  qty: number | null;
  lease_id: number | null;
  invoice_id: number | null;
  status: string;
  notes: string | null;
  created_at: string;
  state: "open" | "resolved";
}

export interface ToolCall {
  tool: string;
  args: unknown;
  result: unknown;
}

export interface Delegation {
  from_agent: AgentName;
  to_agent: AgentName;
  task: string;
  depth: number;
}

export type EventAction =
  | "run_started"
  | "model_step"
  | "delegation_started"
  | "delegation_finished"
  | "delegation_refused"
  | "run_finished"
  | "limit_reached"
  | "error";

export interface AgentEvent {
  timestamp: string;
  run_id: string;
  step: number;
  ticket_id: number | null;
  agent: AgentName;
  depth: number;
  action: EventAction;
  summary: string;
  said: string;
  tools_used: string[];
  tool_calls: ToolCall[];
  delegation: Delegation | null;
  tokens: { input_tokens: number; output_tokens: number; total_tokens: number };
}

export interface PaymentRequest {
  id: number;
  kind: "invoice" | "rent" | "purchase_order";
  ref_id: number;
  amount: number;
  account: string;
  ticket_id: number | null;
  requested_by: string;
  reason: string;
  details: Record<string, unknown> | null;
  status: "pending" | "paid" | "rejected";
  created_at: string;
  decided_by: string | null;
  decided_at: string | null;
  payee: string | null;
}

export interface Cash {
  account: string;
  balance: number;
  date: string;
  pending_requests_total: number;
  balance_after_pending: number;
}

export interface Assignment {
  agent: AgentName;
  did: string;
}

export interface TicketSummary {
  ticket_id: number;
  decision: string;
  assignments: Assignment[];
  waiting_on_human: { item: string; amount: number | null; payment_request_id: number | null }[];
  draft_ids: number[];
  ticket_status: string;
}

export interface RunResult {
  run_id: string;
  ticket_id: number;
  summary?: TicketSummary;
  error?: string;
  ticket_state?: "resolved" | "open";
  unresolved_reason?: string;
}
