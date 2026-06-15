import { useEffect, useRef, useState } from "react";
import type { DocumentDetailResponse } from "../types/documents";

const LIVE_STATUSES = new Set(["queued", "extracting", "analyzing", "evaluating", "recommending"]);

const STAGE_META: Record<string, { label: string; agent: number }> = {
  queued:             { label: "En file d'attente",          agent: 0 },
  starting:           { label: "Démarrage de l'extraction",  agent: 1 },
  selecting_provider: { label: "Sélection du provider",      agent: 1 },
  extracting:         { label: "Extraction du contenu",      agent: 1 },
  normalizing:        { label: "Normalisation du texte",     agent: 1 },
  persisting:         { label: "Sauvegarde extraction",      agent: 1 },
  completed:          { label: "Extraction terminée",        agent: 1 },
  analyzing:          { label: "Démarrage analyse NLP",      agent: 2 },
  segmenting:         { label: "Segmentation des clauses",   agent: 2 },
  classifying:        { label: "Classification des clauses", agent: 2 },
  nlp_persisting:     { label: "Sauvegarde analyse",         agent: 2 },
  nlp_completed:      { label: "Analyse NLP terminée",       agent: 2 },
  evaluating:         { label: "Évaluation juridique",       agent: 3 },
  eval_rules:         { label: "Correspondance des règles",  agent: 3 },
  eval_scoring:       { label: "Calcul du score",            agent: 3 },
  eval_persisting:    { label: "Sauvegarde évaluation",      agent: 3 },
  eval_completed:     { label: "Évaluation terminée",        agent: 3 },
  recommending:       { label: "Génération recommandations", agent: 4 },
  rec_templates:      { label: "Application des templates",  agent: 4 },
  rec_llm:            { label: "Raffinement LLM",            agent: 4 },
  rec_persisting:     { label: "Sauvegarde recommandations", agent: 4 },
  rec_completed:      { label: "Pipeline complet",           agent: 4 },
  failed:             { label: "Échec",                      agent: 0 },
};

const AGENT_LABELS = [
  { label: "Extract",   sub: "Agent 1", color: "teal"    },
  { label: "Analyze",   sub: "Agent 2", color: "violet"  },
  { label: "Evaluate",  sub: "Agent 3", color: "indigo"  },
  { label: "Recommend", sub: "Agent 4", color: "fuchsia" },
];

function agentFromStatus(status: string | undefined): number {
  if (!status) return 0;
  if (["queued", "extracting", "extracted"].includes(status)) return 1;
  if (["analyzing", "analyzed"].includes(status)) return 2;
  if (["evaluating", "evaluated"].includes(status)) return 3;
  if (["recommending", "complete"].includes(status)) return 4;
  return 0;
}

function useSmoothProgress(actual: number, isLive: boolean): number {
  const [display, setDisplay] = useState(actual);
  const actualRef = useRef(actual);

  useEffect(() => {
    actualRef.current = actual;
    setDisplay((prev) => (actual > prev ? actual : prev));
  }, [actual]);

  useEffect(() => {
    if (!isLive) return;
    const id = setInterval(() => {
      setDisplay((prev) => {
        const cap = Math.min(actualRef.current + 10, 97);
        return prev < cap ? parseFloat((prev + 0.12).toFixed(2)) : prev;
      });
    }, 250);
    return () => clearInterval(id);
  }, [isLive]);

  return display;
}

function ElapsedTime({ updatedAt }: { updatedAt: string | null | undefined }) {
  const [elapsed, setElapsed] = useState("");

  useEffect(() => {
    if (!updatedAt) return;
    const update = () => {
      const diff = Math.floor((Date.now() - new Date(updatedAt).getTime()) / 1000);
      if (diff < 5) setElapsed("à l'instant");
      else if (diff < 60) setElapsed(`il y a ${diff}s`);
      else setElapsed(`il y a ${Math.floor(diff / 60)}min`);
    };
    update();
    const id = setInterval(update, 3000);
    return () => clearInterval(id);
  }, [updatedAt]);

  return <span>{elapsed || "—"}</span>;
}

const AGENT_COLORS = {
  teal:    { bar: "from-teal-500 to-teal-400",     badge: "border-teal-400/40 bg-teal-50 text-teal-700",      dot: "bg-teal-500"    },
  violet:  { bar: "from-violet-500 to-violet-400", badge: "border-violet-400/40 bg-violet-50 text-violet-700", dot: "bg-violet-500" },
  indigo:  { bar: "from-indigo-500 to-indigo-400", badge: "border-indigo-400/40 bg-indigo-50 text-indigo-700", dot: "bg-indigo-500" },
  fuchsia: { bar: "from-fuchsia-500 to-fuchsia-400", badge: "border-fuchsia-400/40 bg-fuchsia-50 text-fuchsia-700", dot: "bg-fuchsia-500" },
};

export function ProgressCard({ document }: { document: DocumentDetailResponse | null }) {
  if (!document) {
    return (
      <div className="lex-panel animate-fade-in p-6">
        <p className="text-sm leading-relaxed text-stone-500">
          Sélectionnez un document pour suivre la progression du pipeline en temps réel.
        </p>
      </div>
    );
  }

  const isLive = LIVE_STATUSES.has(document.status);
  const isFailed = document.status === "failed";
  const isComplete = document.status === "complete";

  const smooth = useSmoothProgress(document.progress_percent, isLive);
  const stageMeta = STAGE_META[document.progress_stage] ?? { label: document.progress_stage, agent: 0 };
  const activeAgent = agentFromStatus(document.status);

  return (
    <div className="lex-panel animate-slide-up overflow-hidden">
      {/* Gold accent line at top */}
      <div className={`h-0.5 w-full ${isFailed ? "bg-rose-400" : isComplete ? "bg-gradient-to-r from-emerald-400 to-teal-400" : "bg-gradient-to-r from-gold-500 via-gold-400 to-gold-300"}`} />

      {/* Top section */}
      <div className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gold-600">
                Progression
              </p>
              {isLive && (
                <span className="flex items-center gap-1">
                  <span className="dot-1 h-1 w-1 rounded-full bg-gold-500" />
                  <span className="dot-2 h-1 w-1 rounded-full bg-gold-500" />
                  <span className="dot-3 h-1 w-1 rounded-full bg-gold-500" />
                </span>
              )}
            </div>
            <h2 className="font-display mt-1.5 truncate text-lg font-semibold text-stone-900 sm:text-xl">
              {isFailed ? "Traitement échoué" : isComplete ? "Pipeline terminé" : stageMeta.label}
            </h2>
            {document.progress_message && (
              <p className="mt-1 truncate text-xs leading-relaxed text-stone-500">
                {document.progress_message}
              </p>
            )}
          </div>

          {/* Percentage circle */}
          <div className="flex shrink-0 flex-col items-center">
            <div
              className={`relative flex h-16 w-16 items-center justify-center rounded-full border-2 shadow-inner ${
                isFailed
                  ? "border-rose-300/60 bg-rose-50"
                  : isComplete
                  ? "border-emerald-300/60 bg-emerald-50"
                  : "border-gold-400/50 bg-amber-50 animate-glow-gold"
              }`}
            >
              <span
                className={`font-display text-xl font-bold tabular-nums ${
                  isFailed ? "text-rose-600" : isComplete ? "text-emerald-600" : "text-gold-700"
                }`}
              >
                {Math.round(smooth)}%
              </span>
            </div>
            <p className="mt-1.5 text-[10px] font-semibold uppercase tracking-wide text-stone-500">
              {document.status}
            </p>
          </div>
        </div>

        {/* Main progress bar */}
        <div className="mt-5">
          <div className="h-3 overflow-hidden rounded-full bg-stone-200/80 ring-1 ring-stone-300/50">
            {isFailed ? (
              <div className="h-full w-full rounded-full bg-rose-200" />
            ) : (
              <div
                className={`progress-bar-smooth relative h-full rounded-full bg-gradient-to-r ${
                  isComplete
                    ? "from-emerald-500 via-emerald-400 to-teal-300"
                    : "from-gold-600 via-gold-500 to-gold-300"
                }`}
                style={{ width: `${smooth}%` }}
              >
                {isLive && (
                  <div className="absolute inset-0 animate-progress-stripe rounded-full opacity-50" />
                )}
                {isLive && (
                  <div className="absolute right-0 top-1/2 h-4 w-4 -translate-y-1/2 translate-x-1/2 rounded-full bg-gold-300 blur-sm opacity-80" />
                )}
              </div>
            )}
          </div>
        </div>

        {/* 4-Agent segment indicators */}
        <div className="mt-3 grid grid-cols-4 gap-1.5">
          {AGENT_LABELS.map((ag, i) => {
            const agentNum = i + 1;
            const done = activeAgent > agentNum || isComplete;
            const active = !isFailed && activeAgent === agentNum && !isComplete;
            const colors = AGENT_COLORS[ag.color as keyof typeof AGENT_COLORS];

            return (
              <div
                key={ag.label}
                className={`rounded-lg border px-2 py-1.5 text-center transition-all duration-300 ${
                  isFailed
                    ? "border-stone-200 bg-stone-100/50 opacity-40"
                    : done
                    ? `${colors.badge} opacity-90`
                    : active
                    ? "border-gold-400/60 bg-amber-50 text-gold-800 animate-glow-gold shadow-sm"
                    : "border-stone-200 bg-stone-50/60 opacity-40"
                }`}
              >
                <div className="flex items-center justify-center gap-1">
                  {done && !isFailed && (
                    <svg className="h-2.5 w-2.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {active && (
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold-500" />
                  )}
                </div>
                <p className="mt-0.5 text-[9px] font-bold uppercase tracking-wide leading-none">{ag.label}</p>
                <p className="mt-0.5 text-[8px] opacity-60">{ag.sub}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gold-200/40 bg-amber-50/60 px-5 py-2.5">
        <div className="flex items-center justify-between gap-4 text-[11px] text-stone-500">
          <span>
            Étape :{" "}
            <span className="font-mono text-stone-700">{document.progress_stage}</span>
          </span>
          <span className="flex items-center gap-1">
            <svg className="h-3 w-3 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
            </svg>
            <ElapsedTime updatedAt={document.updated_at} />
          </span>
        </div>
      </div>
    </div>
  );
}
