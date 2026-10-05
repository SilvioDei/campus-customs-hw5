import type { PaymentRequest, Ticket } from "../types";

const TYPE_LABEL: Record<string, string> = {
  customer_order: "Customer order",
  rent_notice: "Rent notice",
  price_override: "Price override",
};

function detail(t: Ticket): string {
  if (t.sku) return `${t.sku} · size ${t.size} · qty ${t.qty}`;
  if (t.lease_id) return `Lease ${t.lease_id}`;
  return t.type;
}

// Tickets hang on the left like paper stubs on a spike: perforated edge,
// a big ticket number, and a rubber stamp once they're resolved.
export function TicketRail({
  tickets,
  selectedId,
  runningId,
  payments,
  onSelect,
}: {
  tickets: Ticket[];
  selectedId: number | null;
  runningId: number | null;
  payments: PaymentRequest[];
  onSelect: (id: number) => void;
}) {
  return (
    <aside className="rail" aria-label="Tickets">
      <h2 className="panel-title">
        <span>Ticket spike</span>
        <span className="count">{tickets.filter((t) => t.state === "open").length} open</span>
      </h2>
      <ol className="stubs">
        {tickets.map((t) => {
          const pending = payments.filter((p) => p.ticket_id === t.id && p.status === "pending").length;
          const running = runningId === t.id;
          return (
            <li key={t.id}>
              <button
                className={`stub${selectedId === t.id ? " is-selected" : ""}${t.state === "resolved" ? " is-resolved" : ""}${running ? " is-running" : ""}`}
                onClick={() => onSelect(t.id)}
                aria-pressed={selectedId === t.id}
              >
                <span className="stub__num">#{t.id}</span>
                <span className="stub__type">{TYPE_LABEL[t.type] ?? t.type}</span>
                <span className="stub__subject">{t.subject}</span>
                <span className="stub__from">from {t.requester}</span>
                <span className="stub__detail">{detail(t)}</span>
                <span className="stub__foot">
                  {running ? (
                    <span className="chip chip--live"><i className="dot" /> crew working</span>
                  ) : (
                    <span className={`chip chip--${t.state}`}>{t.state}</span>
                  )}
                  {pending > 0 && <span className="chip chip--approve">{pending} to approve</span>}
                </span>
                {t.state === "resolved" && <span className="stamp">Resolved</span>}
              </button>
            </li>
          );
        })}
      </ol>
    </aside>
  );
}
