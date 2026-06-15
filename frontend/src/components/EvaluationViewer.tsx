import type { EvaluationResponse, ViolationSchema } from "../types/documents";

const RISK_CONFIG = {
  low:      { label: "Risque faible",    color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-300/50", bar: "bg-emerald-500" },
  medium:   { label: "Risque moyen",     color: "text-amber-700",   bg: "bg-amber-50 border-amber-300/50",     bar: "bg-amber-500" },
  high:     { label: "Risque élevé",     color: "text-orange-700",  bg: "bg-orange-50 border-orange-300/50",   bar: "bg-orange-500" },
  critical: { label: "Risque critique",  color: "text-rose-700",    bg: "bg-rose-50 border-rose-300/50",       bar: "bg-rose-500" },
};

const SEVERITY_CONFIG = {
  critical: { color: "text-rose-700",    bg: "bg-rose-50 border-rose-300/50" },
  high:     { color: "text-orange-700",  bg: "bg-orange-50 border-orange-300/50" },
  medium:   { color: "text-amber-700",   bg: "bg-amber-50 border-amber-300/50" },
  low:      { color: "text-stone-600",   bg: "bg-stone-50 border-stone-300/50" },
};

const FRAMEWORK_COLORS: Record<string, string> = {
  LNPDP:    "text-cyan-700",
  GDPR:     "text-indigo-700",
  ISO27001: "text-violet-700",
  ISO9001:  "text-emerald-700",
};

function ScoreGauge({ score, risk }: { score: number | null; risk: string | null }) {
  const cfg = RISK_CONFIG[risk as keyof typeof RISK_CONFIG] ?? RISK_CONFIG.medium;
  const pct = score ?? 0;
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex items-center gap-5">
      <div className="relative flex h-24 w-24 shrink-0 items-center justify-center">
        <svg className="-rotate-90" width="96" height="96" viewBox="0 0 96 96">
          <circle cx="48" cy="48" r="36" fill="none" stroke="#e7e5e4" strokeWidth="8" />
          <circle
            cx="48" cy="48" r="36" fill="none"
            strokeWidth="8" strokeLinecap="round"
            stroke={pct >= 80 ? "#10b981" : pct >= 60 ? "#f59e0b" : pct >= 40 ? "#f97316" : "#f43f5e"}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        <div className="absolute text-center">
          <p className="text-xl font-bold text-stone-900 leading-none">{pct.toFixed(0)}</p>
          <p className="text-[9px] text-stone-400 uppercase tracking-wide">/ 100</p>
        </div>
      </div>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-widest text-stone-500">Score de conformité</p>
        <p className="mt-1 text-2xl font-bold text-stone-900">{pct.toFixed(1)}<span className="text-base text-stone-400">/100</span></p>
        <span className={`mt-1.5 inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cfg.bg} ${cfg.color}`}>
          {cfg.label}
        </span>
      </div>
    </div>
  );
}

function FrameworkBar({ name, score, count }: { name: string; score: number; count: number }) {
  const color = FRAMEWORK_COLORS[name] ?? "text-stone-600";
  const barColor = score >= 80 ? "bg-emerald-500" : score >= 60 ? "bg-amber-500" : score >= 40 ? "bg-orange-500" : "bg-rose-500";

  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className={`text-xs font-semibold ${color}`}>{name}</span>
        <div className="flex items-center gap-2">
          {count > 0 && (
            <span className="rounded-full bg-rose-50 border border-rose-300/50 px-1.5 py-0.5 text-[10px] text-rose-700">
              {count} violation{count > 1 ? "s" : ""}
            </span>
          )}
          <span className="text-xs font-bold text-stone-800">{score.toFixed(0)}%</span>
        </div>
      </div>
      <div className="h-1.5 w-full rounded-full bg-stone-200">
        <div className={`h-1.5 rounded-full ${barColor} transition-all duration-700`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

function ViolationCard({ v, index }: { v: ViolationSchema; index: number }) {
  const sev = SEVERITY_CONFIG[v.severity as keyof typeof SEVERITY_CONFIG] ?? SEVERITY_CONFIG.medium;
  const fwColor = FRAMEWORK_COLORS[v.framework] ?? "text-stone-600";

  return (
    <div className={`rounded-xl border p-4 ${sev.bg}`}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-stone-200 text-[10px] font-bold text-stone-600">
          {index + 1}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className={`text-[10px] font-bold uppercase tracking-wider ${fwColor}`}>{v.framework}</span>
            <span className="text-stone-300">·</span>
            <span className="text-[10px] text-stone-500">{v.article}</span>
            <span className={`ml-auto rounded-full border px-2 py-0.5 text-[10px] font-semibold ${sev.bg} ${sev.color}`}>
              {v.severity.toUpperCase()}
            </span>
          </div>
          <p className="mt-1 text-sm font-semibold text-stone-900">{v.title}</p>
          <p className="mt-1 text-xs text-stone-600 leading-relaxed">{v.description}</p>
          {v.clause_text && (
            <p className="mt-2 rounded-lg bg-stone-100 border border-stone-200 px-3 py-2 text-[11px] text-stone-600 italic line-clamp-2">
              &ldquo;{v.clause_text}&rdquo;
            </p>
          )}
          {v.remediation_hint && (
            <div className="mt-2 flex items-start gap-1.5">
              <svg className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <p className="text-[11px] text-teal-700">{v.remediation_hint}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function EvaluationViewer({ evaluation }: { evaluation: EvaluationResponse | null }) {
  if (!evaluation) return null;

  const riskCfg = RISK_CONFIG[evaluation.litigation_risk as keyof typeof RISK_CONFIG] ?? RISK_CONFIG.medium;
  const sortedViolations = [...evaluation.violations].sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2, low: 3 };
    return (order[a.severity as keyof typeof order] ?? 4) - (order[b.severity as keyof typeof order] ?? 4);
  });

  return (
    <div className="lex-panel p-5 sm:p-7">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <svg className="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-indigo-700">Agent 3</p>
        <h3 className="font-display text-lg font-medium text-stone-900">Évaluation juridique</h3>
        <span className="rounded-md border border-indigo-300/50 bg-indigo-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest text-indigo-700">
          Règles
        </span>
        <span className={`ml-auto rounded-full border px-2.5 py-0.5 text-xs font-semibold ${riskCfg.bg} ${riskCfg.color}`}>
          {riskCfg.label}
        </span>
      </div>

      {/* Score + frameworks */}
      <div className="grid gap-5 sm:grid-cols-2">
        <ScoreGauge score={evaluation.global_score} risk={evaluation.litigation_risk} />
        <div className="space-y-3">
          {evaluation.active_frameworks.map((fw) => (
            <FrameworkBar
              key={fw}
              name={fw}
              score={evaluation.framework_scores[fw] ?? 100}
              count={evaluation.framework_violation_counts[fw] ?? 0}
            />
          ))}
        </div>
      </div>

      {/* Stats row */}
      <div className="mt-5 grid grid-cols-3 gap-3 border-t border-gold-200/40 pt-5">
        <div className="rounded-xl bg-rose-50 border border-rose-200/60 px-3 py-2.5 text-center">
          <p className="text-xl font-bold text-rose-700">{evaluation.violation_count}</p>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wide text-stone-500">Violations</p>
        </div>
        <div className="rounded-xl bg-amber-50 border border-amber-200/60 px-3 py-2.5 text-center">
          <p className="text-xl font-bold text-amber-700">{evaluation.missing_clauses.length}</p>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wide text-stone-500">Clauses manquantes</p>
        </div>
        <div className="rounded-xl bg-teal-50 border border-teal-200/60 px-3 py-2.5 text-center">
          <p className="text-xl font-bold text-teal-700">{evaluation.active_frameworks.length}</p>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wide text-stone-500">Référentiels</p>
        </div>
      </div>

      {/* Missing clauses */}
      {evaluation.missing_clauses.length > 0 && (
        <div className="mt-4 rounded-xl border border-amber-300/50 bg-amber-50 p-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-amber-700">Clauses obligatoires manquantes</p>
          <div className="flex flex-wrap gap-1.5">
            {evaluation.missing_clauses.map((key) => (
              <span key={key} className="rounded-full border border-amber-300/50 bg-white px-2.5 py-0.5 text-[11px] text-amber-800">
                {key.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Violations list */}
      {sortedViolations.length > 0 && (
        <div className="mt-5">
          <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-stone-500">
            Violations ({sortedViolations.length})
          </p>
          <div className="space-y-3">
            {sortedViolations.map((v, i) => (
              <ViolationCard key={v.violation_id} v={v} index={i} />
            ))}
          </div>
        </div>
      )}

      {sortedViolations.length === 0 && (
        <div className="mt-5 flex items-center gap-2 rounded-xl border border-emerald-300/50 bg-emerald-50 px-4 py-3">
          <svg className="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <p className="text-sm text-emerald-800">Aucune violation détectée — le contrat est conforme.</p>
        </div>
      )}
    </div>
  );
}
