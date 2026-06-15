import { useState } from "react";

import type { DocumentStatus, RecommendationItem } from "../types/documents";

function sourceBadge(generatedBy: string | null | undefined): { label: string; className: string } | null {
  const g = (generatedBy || "").toLowerCase();
  if (g === "llm_v2" || g.includes("groq") || g === "groq_llm_v1") {
    return {
      label: "AI Enhanced",
      className: "border-violet-300/50 bg-violet-50 text-violet-700",
    };
  }
  if (g.includes("template")) {
    return { label: "Template", className: "border-stone-300/50 bg-stone-100 text-stone-600" };
  }
  if (g.includes("fallback")) {
    return { label: "Fallback", className: "border-amber-300/50 bg-amber-50 text-amber-700" };
  }
  return generatedBy
    ? { label: generatedBy, className: "border-stone-300/50 bg-stone-100 text-stone-500" }
    : null;
}

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-rose-50 text-rose-700 border-rose-300/50",
  high:     "bg-orange-50 text-orange-700 border-orange-300/50",
  medium:   "bg-amber-50 text-amber-700 border-amber-300/50",
  low:      "bg-stone-100 text-stone-600 border-stone-300/50",
};

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      className={`h-4 w-4 shrink-0 text-stone-400 transition-transform ${open ? "rotate-180" : ""}`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
    </svg>
  );
}

function RecommendationCard({ item }: { item: RecommendationItem }) {
  const [open, setOpen] = useState(false);
  const sev = (item.severity || "medium").toLowerCase();
  const badge = SEVERITY_BADGE[sev] ?? SEVERITY_BADGE.medium;
  const srcBadge = sourceBadge(item.generated_by);

  return (
    <div className="overflow-hidden rounded-xl border border-stone-200 bg-white/80 shadow-sm">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-start gap-3 px-4 py-3 text-left transition hover:bg-amber-50/50"
      >
        <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-fuchsia-50 border border-fuchsia-200 text-xs font-bold text-fuchsia-700">
          {item.priority ?? "—"}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-wide text-teal-700">
              {item.framework || "—"} {item.article ? `· ${item.article}` : ""}
            </span>
            <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase ${badge}`}>
              {item.severity || "—"}
            </span>
            {srcBadge && (
              <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase ${srcBadge.className}`}>
                {srcBadge.label}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm font-medium text-stone-900 line-clamp-2">{item.issue_description || "—"}</p>
          {item.clause_id && (
            <p className="mt-0.5 text-[11px] text-stone-500">Clause {item.clause_id}</p>
          )}
        </div>
        <Chevron open={open} />
      </button>
      {open && (
        <div className="space-y-3 border-t border-stone-200/70 bg-stone-50/60 px-4 py-3 text-sm">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-500">Action</p>
            <p className="mt-1 text-stone-800 leading-relaxed">{item.recommendation_text || "—"}</p>
          </div>
          {item.rewritten_clause && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-500">Clause proposée</p>
              <pre className="mt-1 whitespace-pre-wrap rounded-lg border border-stone-200 bg-stone-100 p-3 text-xs text-stone-700 leading-relaxed font-mono">
                {item.rewritten_clause}
              </pre>
            </div>
          )}
          {item.legal_rationale && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-500">Base juridique</p>
              <p className="mt-1 text-stone-600 leading-relaxed">{item.legal_rationale}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function RecommendationViewer({
  documentId,
  status,
  data,
  agent4LlmEnabled = null,
}: {
  documentId: number;
  status: DocumentStatus | undefined;
  data: { total: number; recommendations: RecommendationItem[] } | null;
  agent4LlmEnabled?: boolean | null;
}) {
  const loading = status === "recommending";
  const waitingAfterEval = status === "evaluated" && data != null && data.total === 0;

  return (
    <div className="lex-panel p-6 sm:p-7 ring-1 ring-fuchsia-300/20">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-fuchsia-700">Agent 4</p>
          <h2 className="font-display mt-1 text-xl font-medium text-stone-900">Recommandations</h2>
          <p className="mt-1 text-xs text-stone-500">
            Templates issus des règles d'évaluation
            {agent4LlmEnabled === true ? " · Mode hybride actif : LLM Groq disponible." : ""}
            {agent4LlmEnabled === false ? " · Templates uniquement : LLM_API_KEY non configuré." : ""}
            {agent4LlmEnabled === null ? " · Statut LLM inconnu." : ""}
            {" "}· document #{documentId}
          </p>
        </div>
        {data != null && (
          <span className="rounded-full border border-fuchsia-300/50 bg-fuchsia-50 px-3 py-1 text-xs font-bold text-fuchsia-700">
            {data.total} item{data.total === 1 ? "" : "s"}
          </span>
        )}
      </div>

      {loading && (
        <p className="mt-4 text-sm text-amber-700">
          Génération des recommandations en cours… Cela prend généralement quelques secondes après l'évaluation.
        </p>
      )}

      {waitingAfterEval && !loading && (
        <p className="mt-4 text-sm text-stone-500">
          Les recommandations sont en file d'attente. Actualisez dans un instant si le pipeline est encore en cours.
        </p>
      )}

      {!loading && !waitingAfterEval && data && data.total === 0 && (
        <p className="mt-4 text-sm text-stone-500">
          Aucune recommandation générée (aucune violation ou liste vide).
        </p>
      )}

      {data && data.recommendations.length > 0 && (
        <div className="mt-4 space-y-3">
          {data.recommendations.map((item) => (
            <RecommendationCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
