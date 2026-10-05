// Every call the desk makes goes to the FastAPI backend from Problem 7.
import type { AgentEvent, Cash, PaymentRequest, RunResult, Ticket } from "./types";

export const API_BASE = "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function detailText(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d?.msg ?? String(d)).join("; ");
  return `Request failed (HTTP ${status})`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(API_BASE + path, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(0, `Can't reach the backend at ${API_BASE}. Is uvicorn running?`);
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, detailText(body, res.status));
  return body as T;
}

export const api = {
  health: () => request<{ status: string }>("/"),
  tickets: () => request<{ tickets: Ticket[] }>("/tickets").then((r) => r.tickets),
  runTicket: (id: number) => request<RunResult>(`/tickets/${id}/run`, { method: "POST" }),
  events: (ticketId: number, limit = 400) =>
    request<{ events: AgentEvent[]; total: number }>(`/events?ticket_id=${ticketId}&limit=${limit}`).then((r) => r.events),
  payments: (status: "pending" | "paid" | "rejected" | "all" = "all") =>
    request<{ requests: PaymentRequest[] }>(`/payments?status=${status}`).then((r) => r.requests),
  approve: (requestId: number, approvedBy: string) =>
    request<{ paid: boolean; amount: number }>(`/payments/${requestId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved_by: approvedBy }),
    }),
  cash: () => request<Cash>("/cash"),
  reset: () => request<{ reset: boolean }>("/reset", { method: "POST" }),
};
