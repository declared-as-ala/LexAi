import type { DocumentSummaryResponse } from "../types/documents";

const STATUS_CARDS = [
  { key: "complete_count",     label: "Complets",    color: "text-emerald-700", bg: "bg-emerald-50",  border: "border-emerald-300/50", dot: "bg-emerald-500" },
  { key: "failed_count",       label: "Échecs",      color: "text-rose-700",    bg: "bg-rose-50",     border: "border-rose-300/50",    dot: "bg-rose-500" },
  { key: "queued_count",       label: "En attente",  color: "text-amber-700",   bg: "bg-amber-50",    border: "border-amber-300/50",   dot: "bg-amber-500 animate-pulse" },
  { key: "extracting_count",   label: "Extraction",  color: "text-sky-700",     bg: "bg-sky-50",      border: "border-sky-300/50",     dot: "bg-sky-500 animate-pulse" },
  { key: "analyzing_count",    label: "Analyse",     color: "text-violet-700",  bg: "bg-violet-50",   border: "border-violet-300/50",  dot: "bg-violet-500 animate-pulse" },
  { key: "evaluating_count",   label: "Évaluation",  color: "text-indigo-700",  bg: "bg-indigo-50",   border: "border-indigo-300/50",  dot: "bg-indigo-500 animate-pulse" },
  { key: "recommending_count", label: "Recommande",  color: "text-fuchsia-700", bg: "bg-fuchsia-50",  border: "border-fuchsia-300/50", dot: "bg-fuchsia-500 animate-pulse" },
  { key: "extracted_count",    label: "Extraits",    color: "text-teal-700",    bg: "bg-teal-50",     border: "border-teal-300/50",    dot: "bg-teal-500" },
] as const;

const AGENT_RATES = [
  { label: "Agent 1", key: "agent1_success_rate", color: "text-teal-700",    bar: "bg-teal-400",    border: "border-teal-300/40",    bg: "bg-teal-50" },
  { label: "Agent 2", key: "agent2_success_rate", color: "text-violet-700",  bar: "bg-violet-400",  border: "border-violet-300/40",  bg: "bg-violet-50" },
  { label: "Agent 3", key: "agent3_success_rate", color: "text-indigo-700",  bar: "bg-indigo-400",  border: "border-indigo-300/40",  bg: "bg-indigo-50" },
  { label: "Agent 4", key: "agent4_success_rate", color: "text-fuchsia-700", bar: "bg-fuchsia-400", border: "border-fuchsia-300/40", bg: "bg-fuchsia-50" },
] as const;

export function QueueSummaryCards({ summary }: { summary: DocumentSummaryResponse | null }) {
  const total = summary?.total_count ?? 0;
  const hasActivity = total > 0;

  return (
    <div className="lex-panel animate-slide-up p-4 sm:p-5">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between gap-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">Débit</p>
          <p className="mt-0.5 text-sm font-semibold text-stone-900">Vue d'ensemble</p>
        </div>
        <div className="flex items-center gap-2">
          {hasActivity && (
            <span className="h-2 w-2 animate-pulse rounded-full bg-gold-500" />
          )}
          <span className="rounded-full border border-gold-300/40 bg-amber-50 px-3 py-1 text-xs font-bold tabular-nums text-gold-700">
            {total} doc{total !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Status grid */}
      <div className="grid grid-cols-4 gap-1.5">
        {STATUS_CARDS.map((card) => {
          const value = summary?.[card.key] ?? 0;
          return (
            <div
              key={card.key}
              className={`rounded-xl border p-2.5 transition-all duration-200 ${card.border} ${card.bg} ${
                value === 0 ? "opacity-40" : "opacity-100"
              }`}
            >
              <div className="flex items-center gap-1">
                <span className={`h-1.5 w-1.5 rounded-full ${card.dot}`} />
              </div>
              <p className={`font-display mt-1 text-xl font-bold tabular-nums ${card.color}`}>
                {value}
              </p>
              <p className="mt-0.5 text-[9px] font-semibold uppercase tracking-wide text-stone-500 leading-tight">
                {card.label}
              </p>
            </div>
          );
        })}
      </div>

      {/* Agent success rates */}
      <div className="mt-4 space-y-2">
        <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-stone-500">
          Taux de succès
        </p>
        <div className="grid grid-cols-2 gap-2">
          {AGENT_RATES.map((ag) => {
            const rate = summary?.[ag.key] ?? 0;
            return (
              <div
                key={ag.key}
                className={`rounded-lg border p-2.5 ${ag.border} ${ag.bg}`}
              >
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-500">
                    {ag.label}
                  </p>
                  <p className={`font-display text-sm font-bold tabular-nums ${ag.color}`}>
                    {rate}%
                  </p>
                </div>
                <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-stone-200/80">
                  <div
                    className={`progress-bar-smooth h-full rounded-full ${ag.bar}`}
                    style={{ width: `${rate}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
