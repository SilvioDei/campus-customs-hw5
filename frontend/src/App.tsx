import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError, API_BASE } from "./api";
import { latestRun } from "./runlog";
import type { AgentEvent, Cash, PaymentRequest, RunResult, Ticket } from "./types";
import { TicketRail } from "./components/TicketRail";
import { CrewStage } from "./components/CrewStage";
import { EventFeed } from "./components/EventFeed";
import { RunSummary } from "./components/RunSummary";
import { ApprovalTray, CashDrawer } from "./components/Register";

const POLL_MS = 2500;
const SIGNER_KEY = "cc-desk-signer";
const RESET_KEY = "cc-desk-last-reset";

const errText = (e: unknown) => (e instanceof ApiError ? e.message : String(e));

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [payments, setPayments] = useState<PaymentRequest[]>([]);
  const [cash, setCash] = useState<Cash | null>(null);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [results, setResults] = useState<Record<number, RunResult>>({});
  const [online, setOnline] = useState<boolean | null>(null);
  const [toast, setToast] = useState<{ text: string; tone: "ok" | "bad" } | null>(null);
  const [signer, setSigner] = useState(() => localStorage.getItem(SIGNER_KEY) ?? "");
  const [lastReset, setLastReset] = useState(() => localStorage.getItem(RESET_KEY));
  const [resetArmed, setResetArmed] = useState(false);

  const say = (text: string, tone: "ok" | "bad" = "ok") => setToast({ text, tone });

  const refreshBoard = useCallback(async () => {
    try {
      const [t, p, c] = await Promise.all([api.tickets(), api.payments("all"), api.cash()]);
      setTickets(t);
      setPayments(p);
      setCash(c);
      setOnline(true);
      setSelectedId((id) => id ?? t[0]?.id ?? null);
    } catch (e) {
      setOnline(false);
      say(errText(e), "bad");
    }
  }, []);

  // Only apply an events response if its ticket is still the one on screen, so a
  // slow reply for a ticket you clicked away from can't overwrite the feed.
  const selectedRef = useRef<number | null>(null);
  selectedRef.current = selectedId;

  const refreshEvents = useCallback(async (ticketId: number | null) => {
    if (ticketId == null) return;
    try {
      const evs = await api.events(ticketId);
      if (selectedRef.current === ticketId) setEvents(evs);
    } catch {
      /* the board banner already shows the backend is down */
    }
  }, []);

  useEffect(() => {
    refreshBoard();
  }, [refreshBoard]);

  useEffect(() => {
    setEvents([]);
    refreshEvents(selectedId);
  }, [selectedId, refreshEvents]);

  const run = useMemo(() => latestRun(events), [events]);
  // A run is live if this tab started it, or the trail shows one still going
  // (ignoring an unfinished run that has been silent for 10 minutes, e.g. a crash).
  const lastAt = run?.events[run.events.length - 1]?.timestamp;
  const recent = !!lastAt && Date.now() - Date.parse(lastAt) < 10 * 60 * 1000;
  const live = runningId != null ? runningId === selectedId : !!run && !run.finished && recent;

  useEffect(() => {
    if (!live && runningId == null) return;
    const id = setInterval(() => {
      refreshEvents(selectedId);
      refreshBoard();
    }, POLL_MS);
    return () => clearInterval(id);
  }, [live, runningId, selectedId, refreshEvents, refreshBoard]);

  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 6000);
    return () => clearTimeout(id);
  }, [toast]);

  async function startRun(ticketId: number) {
    setRunningId(ticketId);
    setSelectedId(ticketId);
    say(`Crew is on ticket #${ticketId}. Watch them work in the feed.`);
    try {
      const result = await api.runTicket(ticketId);
      setResults((r) => ({ ...r, [ticketId]: result }));
      if (result.error) say(`Ticket #${ticketId} stopped: ${result.error}`, "bad");
      else if (result.unresolved_reason) say(`Ticket #${ticketId} not resolved yet. ${result.unresolved_reason}`, "bad");
      else say(`Ticket #${ticketId} resolved. Check the handover and anything waiting for your signature.`);
    } catch (e) {
      say(`Run failed: ${errText(e)}`, "bad");
    } finally {
      setRunningId(null);
      await Promise.all([refreshBoard(), refreshEvents(ticketId)]);
    }
  }

  async function approve(requestId: number): Promise<string | null> {
    try {
      const res = await api.approve(requestId, signer.trim());
      say(`Paid ${res.amount.toLocaleString("en-US", { style: "currency", currency: "USD" })}. Signed by ${signer.trim()}.`);
      return null;
    } catch (e) {
      return errText(e);
    } finally {
      await refreshBoard();
    }
  }

  async function reset() {
    if (!resetArmed) {
      setResetArmed(true);
      setTimeout(() => setResetArmed(false), 4000);
      return;
    }
    setResetArmed(false);
    try {
      await api.reset();
      const now = new Date().toISOString();
      localStorage.setItem(RESET_KEY, now);
      setLastReset(now);
      setResults({});
      await Promise.all([refreshBoard(), refreshEvents(selectedId)]);
      say("Fresh day. The working database was reset from the original.");
    } catch (e) {
      say(`Reset refused: ${errText(e)}`, "bad");
    }
  }

  function updateSigner(name: string) {
    setSigner(name);
    localStorage.setItem(SIGNER_KEY, name);
  }

  const selected = tickets.find((t) => t.id === selectedId) ?? null;
  const liveSummary = selectedId != null ? results[selectedId] : undefined;
  const summary = liveSummary?.run_id === run?.runId && liveSummary?.summary ? liveSummary.summary : run?.summary ?? null;
  const stale = !!(run && lastReset && run.startedAt < lastReset);
  const openCount = tickets.filter((t) => t.state === "open").length;

  return (
    <div className="desk">
      <header className="topbar">
        <div className="brand">
          <span className="neon">Campus Customs</span>
          <span className="brand__sub">night desk · agent operations</span>
        </div>
        <div className="topbar__status">
          <span className={`pill ${online ? "pill--on" : online === false ? "pill--off" : ""}`}>
            <i className="dot" /> {online ? "backend online" : online === false ? `backend offline · ${API_BASE}` : "connecting…"}
          </span>
          <span className="pill">{openCount} open · {tickets.length - openCount} resolved</span>
          {cash && <span className="pill">shop day {cash.date}</span>}
          <button className={`btn btn--reset${resetArmed ? " is-armed" : ""}`} onClick={reset} disabled={runningId != null}>
            {resetArmed ? "Click again to reset" : "↺ Reset the day"}
          </button>
        </div>
      </header>

      <TicketRail
        tickets={tickets}
        selectedId={selectedId}
        runningId={runningId}
        payments={payments}
        onSelect={setSelectedId}
      />

      <main className="floor">
        {selected ? (
          <>
            <section className="brief">
              <div>
                <div className="brief__eyebrow">Ticket #{selected.id} · {selected.requester}</div>
                <h1 className="brief__title">{selected.subject}</h1>
                {selected.notes && <p className="brief__notes">“{selected.notes}”</p>}
              </div>
              <button
                className="btn btn--go"
                onClick={() => startRun(selected.id)}
                disabled={runningId != null || selected.state === "resolved" || live}
              >
                {runningId === selected.id || live
                  ? "Crew working…"
                  : selected.state === "resolved"
                    ? "Resolved · reset to run again"
                    : runningId != null
                      ? `Crew busy on #${runningId}`
                      : "▶ Start the crew"}
              </button>
            </section>

            <CrewStage run={run} running={live} />

            {liveSummary?.unresolved_reason && liveSummary.run_id === run?.runId && (
              <div className="notice notice--bad" role="alert">
                <b>Not resolved yet.</b> {liveSummary.unresolved_reason}
              </div>
            )}

            <RunSummary summary={summary} run={run} stale={stale} />

            <section className="transcript">
              <h2 className="panel-title">
                <span>Live floor</span>
                <span className="count">
                  {run ? `run ${run.runId}${run.olderRuns ? ` · ${run.olderRuns} earlier` : ""}` : "no runs yet"}
                </span>
              </h2>
              <EventFeed events={run?.events ?? []} running={live} />
            </section>
          </>
        ) : (
          <p className="muted">Loading tickets…</p>
        )}
      </main>

      <aside className="register">
        <CashDrawer cash={cash} />
        <ApprovalTray requests={payments} signer={signer} onSigner={updateSigner} onApprove={approve} />
      </aside>

      {toast && (
        <div className={`toast toast--${toast.tone}`} role="status" onClick={() => setToast(null)}>
          {toast.text}
        </div>
      )}
    </div>
  );
}
