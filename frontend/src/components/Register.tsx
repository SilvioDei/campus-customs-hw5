import { useEffect, useRef, useState } from "react";
import { money } from "../agents";
import type { Cash, PaymentRequest } from "../types";

const KIND_LABEL: Record<PaymentRequest["kind"], string> = {
  invoice: "Vendor invoice",
  rent: "Rent",
  purchase_order: "Purchase order",
};

function refLabel(p: PaymentRequest): string {
  if (p.kind === "invoice") return `invoice #${p.ref_id}`;
  if (p.kind === "rent") return `lease #${p.ref_id}`;
  const d = p.details as { sku?: string; size?: string; qty?: number } | null;
  return d ? `${d.qty} × ${d.sku} (${d.size})` : `vendor #${p.ref_id}`;
}

// The cash drawer: a glowing register display that ticks down when a human
// approves a payment, with the paid slips printed on a receipt tape below.
export function CashDrawer({ cash }: { cash: Cash | null }) {
  const prev = useRef<number | null>(null);
  const [drop, setDrop] = useState<{ amount: number; key: number } | null>(null);

  useEffect(() => {
    if (cash == null) return;
    if (prev.current != null && cash.balance < prev.current) {
      setDrop({ amount: prev.current - cash.balance, key: Date.now() });
    }
    prev.current = cash.balance;
  }, [cash?.balance]);

  const tight = cash != null && cash.balance_after_pending < 0;
  return (
    <section className="drawer" aria-label="Checking balance">
      <h2 className="panel-title"><span>Cash drawer</span><span className="count">checking</span></h2>
      <div className={`lcd${tight ? " is-tight" : ""}`}>
        <span className="lcd__label">BALANCE</span>
        <span className="lcd__value">{cash ? money(cash.balance) : "— — —"}</span>
        {drop && (
          <span key={drop.key} className="lcd__drop" onAnimationEnd={() => setDrop(null)}>
            −{money(drop.amount)}
          </span>
        )}
      </div>
      {cash && (
        <dl className="drawer__stats">
          <div><dt>Waiting on approval</dt><dd>{money(cash.pending_requests_total)}</dd></div>
          <div className={tight ? "is-tight" : ""}>
            <dt>Left if all approved</dt><dd>{money(cash.balance_after_pending)}</dd>
          </div>
          <div><dt>As of shop day</dt><dd>{cash.date}</dd></div>
        </dl>
      )}
      {tight && <p className="drawer__warn">Not everything waiting can be paid. Someone has to choose.</p>}
    </section>
  );
}

export function ApprovalTray({
  requests,
  signer,
  onSigner,
  onApprove,
}: {
  requests: PaymentRequest[];
  signer: string;
  onSigner: (name: string) => void;
  onApprove: (id: number) => Promise<string | null>;
}) {
  const [refusals, setRefusals] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);
  const pending = requests.filter((r) => r.status === "pending");
  const paid = requests.filter((r) => r.status === "paid");

  async function approve(id: number) {
    setBusy(id);
    const refusal = await onApprove(id);
    setBusy(null);
    setRefusals((r) => {
      const next = { ...r };
      if (refusal) next[id] = refusal;
      else delete next[id];
      return next;
    });
  }

  return (
    <section className="tray" aria-label="Approvals">
      <h2 className="panel-title">
        <span>Needs your signature</span>
        <span className="count">{pending.length}</span>
      </h2>
      <label className="signer">
        <span>Signing as</span>
        <input value={signer} onChange={(e) => onSigner(e.target.value)} placeholder="your name" />
      </label>
      {pending.length === 0 && (
        <p className="tray__empty">Nothing to sign. Agents only prepare payments; they land here for a human.</p>
      )}
      <ul className="slips">
        {pending.map((r) => (
          <li key={r.id} className={`slip${refusals[r.id] ? " is-refused" : ""}`}>
            <div className="slip__top">
              <span className="slip__kind">{KIND_LABEL[r.kind]}</span>
              <span className="slip__id">#{r.id}{r.ticket_id != null && ` · ticket ${r.ticket_id}`}</span>
            </div>
            <div className="slip__payee">Pay to <b>{r.payee ?? "unknown payee"}</b></div>
            <div className="slip__amount">{money(r.amount)}</div>
            <div className="slip__ref">{refLabel(r)} · from {r.account}</div>
            <p className="slip__why"><span>Why</span>{r.reason}</p>
            <div className="slip__by">prepared by {r.requested_by}</div>
            {refusals[r.id] && (
              <div className="slip__refusal" role="alert">
                <b>Refused</b> {refusals[r.id].replace(/^Refused:\s*/i, "")}
              </div>
            )}
            <button
              className="btn btn--approve"
              disabled={busy === r.id || !signer.trim()}
              onClick={() => approve(r.id)}
              title={signer.trim() ? "" : "Type your name above to sign"}
            >
              {busy === r.id ? "Paying…" : `Approve & pay ${money(r.amount)}`}
            </button>
          </li>
        ))}
      </ul>
      {paid.length > 0 && (
        <div className="tape" aria-label="Paid today">
          <div className="tape__head">· · · PAID · · ·</div>
          {paid.map((r) => (
            <div key={r.id} className="tape__row">
              <span>{KIND_LABEL[r.kind]} → {r.payee ?? "—"}</span>
              <span>−{money(r.amount)}</span>
              <span className="tape__sig">signed {r.decided_by}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
