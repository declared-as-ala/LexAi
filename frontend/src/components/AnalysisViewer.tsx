import { useState } from "react";
import type { ClauseAnalysis, NLPAnalysisResponse } from "../types/documents";

const LABEL_COLORS: Record<string, string> = {
  data_processing:  "bg-blue-50 text-blue-700 border-blue-300/50",
  confidentiality:  "bg-purple-50 text-purple-700 border-purple-300/50",
  liability:        "bg-orange-50 text-orange-700 border-orange-300/50",
  termination:      "bg-red-50 text-red-700 border-red-300/50",
  obligation:       "bg-cyan-50 text-cyan-700 border-cyan-300/50",
  penalty:          "bg-rose-50 text-rose-700 border-rose-300/50",
  payment:          "bg-green-50 text-green-700 border-green-300/50",
  dispute_resolution: "bg-yellow-50 text-yellow-800 border-yellow-300/50",
  force_majeure:    "bg-stone-100 text-stone-600 border-stone-300/50",
  ip_rights:        "bg-indigo-50 text-indigo-700 border-indigo-300/50",
  warranty:         "bg-teal-50 text-teal-700 border-teal-300/50",
  definition:       "bg-stone-100 text-stone-600 border-stone-300/50",
};

const FLAG_COLORS: Record<string, string> = {
  lnpdp_relevant:               "bg-amber-50 text-amber-700 border-amber-300/50",
  gdpr_relevant:                "bg-amber-50 text-amber-700 border-amber-300/50",
  missing_retention_period:     "bg-rose-50 text-rose-700 border-rose-300/50",
  missing_consent_mechanism:    "bg-rose-50 text-rose-700 border-rose-300/50",
  missing_security_measures:    "bg-rose-50 text-rose-700 border-rose-300/50",
  missing_dpo_reference:        "bg-rose-50 text-rose-700 border-rose-300/50",
  missing_data_subject_rights:  "bg-rose-50 text-rose-700 border-rose-300/50",
  unlawful_cross_border_transfer: "bg-red-50 text-red-700 border-red-300/50",
  unclear_liability_cap:        "bg-orange-50 text-orange-700 border-orange-300/50",
  excessive_data_collection:    "bg-red-50 text-red-700 border-red-300/50",
};

const ENTITY_COLORS: Record<string, string> = {
  PARTY:        "bg-sky-50 text-sky-700",
  ROLE:         "bg-teal-50 text-teal-700",
  DATA_CATEGORY:"bg-blue-50 text-blue-700",
  DURATION:     "bg-green-50 text-green-700",
  AMOUNT:       "bg-yellow-50 text-yellow-800",
  LAW_REFERENCE:"bg-purple-50 text-purple-700",
  JURISDICTION: "bg-orange-50 text-orange-700",
  DATE:         "bg-pink-50 text-pink-700",
};

function Badge({ text, colorClass }: { text: string; colorClass: string }) {
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${colorClass}`}>
      {text.replace(/_/g, " ")}
    </span>
  );
}

function ClauseCard({ clause }: { clause: ClauseAnalysis }) {
  const [expanded, setExpanded] = useState(false);
  const hasFlags = clause.compliance_flags.length > 0;

  return (
    <div
      className={`rounded-xl border transition-colors ${
        hasFlags
          ? "border-amber-300/50 bg-amber-50/60"
          : "border-stone-200 bg-white/70"
      }`}
    >
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-start justify-between gap-4 p-4 text-left"
      >
        <div className="flex min-w-0 flex-col gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-stone-400">{clause.clause_id}</span>
            {clause.section_title && (
              <span className="truncate text-sm font-medium text-stone-800">{clause.section_title}</span>
            )}
            {hasFlags && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700 border border-amber-300/50">
                {clause.compliance_flags.length} flag{clause.compliance_flags.length > 1 ? "s" : ""}
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-1">
            {clause.labels.map((label) => (
              <Badge key={label} text={label} colorClass={LABEL_COLORS[label] ?? "bg-stone-100 text-stone-600 border-stone-300/50"} />
            ))}
          </div>
        </div>
        <span className="mt-1 shrink-0 text-stone-400">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="border-t border-stone-200/70 px-4 pb-4 pt-3 space-y-4">
          <pre className="max-h-48 overflow-auto rounded-lg bg-stone-100 border border-stone-200 p-3 text-xs text-stone-700 whitespace-pre-wrap leading-relaxed font-mono">
            {clause.text}
          </pre>

          {clause.compliance_flags.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-amber-700">Flags de conformité</p>
              <div className="flex flex-wrap gap-1">
                {clause.compliance_flags.map((flag) => (
                  <Badge key={flag} text={flag} colorClass={FLAG_COLORS[flag] ?? "bg-rose-50 text-rose-700 border-rose-300/50"} />
                ))}
              </div>
            </div>
          )}

          {clause.entities.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-stone-500">Entités détectées</p>
              <div className="flex flex-wrap gap-1.5">
                {clause.entities.map((entity, i) => (
                  <span
                    key={i}
                    className={`inline-flex items-center gap-1.5 rounded-md border border-current/20 px-2 py-0.5 text-xs ${ENTITY_COLORS[entity.label] ?? "bg-stone-100 text-stone-600"}`}
                  >
                    <span className="font-medium">{entity.text}</span>
                    <span className="opacity-50">·</span>
                    <span className="opacity-70">{entity.label}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs text-stone-500">
            Modèle : <span className="text-stone-700">{clause.model_used}</span>
            {" · "}
            {clause.model_used === "heuristic" ? (
              <>Correspondance : {(clause.confidence * 100).toFixed(0)}% <span className="text-stone-400">(règles mot-clé)</span></>
            ) : (
              <>Confiance : {(clause.confidence * 100).toFixed(0)}%</>
            )}
          </p>
        </div>
      )}
    </div>
  );
}

const RISK_COLORS: Record<string, string> = {
  low:      "border-emerald-300/50 bg-emerald-50 text-emerald-700",
  medium:   "border-amber-300/50 bg-amber-50 text-amber-700",
  high:     "border-orange-300/50 bg-orange-50 text-orange-700",
  critical: "border-red-300/50 bg-red-50 text-red-700",
};

const SCORE_BAR_COLOR: Record<string, string> = {
  low:      "bg-emerald-500",
  medium:   "bg-amber-500",
  high:     "bg-orange-500",
  critical: "bg-red-500",
};

function RiskBanner({ riskLevel, score }: { riskLevel: string | null; score: number | null }) {
  if (!riskLevel) return null;
  const color = RISK_COLORS[riskLevel] ?? RISK_COLORS.medium;
  const barColor = SCORE_BAR_COLOR[riskLevel] ?? SCORE_BAR_COLOR.medium;
  const pct = score ?? 0;

  return (
    <div className={`rounded-xl border p-4 ${color}`}>
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest opacity-60">Niveau de risque</p>
          <p className="text-xl font-bold capitalize">{riskLevel}</p>
        </div>
        {score !== null && (
          <div className="flex flex-col items-end gap-1 min-w-[120px]">
            <p className="text-xs font-semibold uppercase tracking-widest opacity-60">Score de conformité</p>
            <p className="text-xl font-bold">{pct.toFixed(0)}/100</p>
            <div className="h-1.5 w-full rounded-full bg-black/10">
              <div className={`h-1.5 rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatBadge({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={`rounded-lg border px-3 py-2 text-center ${color}`}>
      <p className="text-lg font-bold">{value}</p>
      <p className="text-xs opacity-60">{label}</p>
    </div>
  );
}

export function AnalysisViewer({ analysis }: { analysis: NLPAnalysisResponse | null }) {
  const [labelFilter, setLabelFilter] = useState<string>("all");
  const [flagFilter, setFlagFilter] = useState<string>("all");

  if (!analysis) return null;

  const flaggedCount = analysis.clauses.filter((c) => c.compliance_flags.length > 0).length;
  const allLabels = [...new Set(analysis.clauses.flatMap((c) => c.labels))].sort();
  const allFlags  = [...new Set(analysis.clauses.flatMap((c) => c.compliance_flags))].sort();

  const filtered = analysis.clauses.filter((c) => {
    if (labelFilter !== "all" && !c.labels.includes(labelFilter)) return false;
    if (flagFilter !== "all" && !c.compliance_flags.includes(flagFilter)) return false;
    return true;
  });

  return (
    <div className="lex-panel space-y-6 p-6 sm:p-7">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-violet-700">Agent 2</p>
          <h2 className="font-display mt-1 text-xl font-medium text-stone-900 sm:text-2xl">Analyse NLP</h2>
          <p className="mt-1 text-sm text-stone-500">
            Classifier :{" "}
            <span className="font-medium text-stone-700">{analysis.model_used ?? "heuristic"}</span>
            {(analysis.model_used ?? "heuristic") === "heuristic" && (
              <span className="block mt-1 text-xs text-stone-400 max-w-xl">
                Aucun pipeline Hugging Face actif — les étiquettes proviennent de règles de mots-clés.
              </span>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {analysis.language && (
            <span className="rounded-full border border-stone-300/50 bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-700">
              {analysis.language.toUpperCase()}
            </span>
          )}
          <span className="rounded-full border border-violet-300/50 bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">
            {analysis.clause_count} clauses
          </span>
        </div>
      </div>

      <RiskBanner riskLevel={analysis.risk_level} score={analysis.compliance_score} />

      <div className="grid grid-cols-3 gap-3">
        <StatBadge label="Clauses"  value={analysis.clause_count}              color="border-stone-200 text-stone-700 bg-stone-50" />
        <StatBadge label="Flaggées" value={flaggedCount}
          color={flaggedCount > 0 ? "border-amber-300/50 text-amber-700 bg-amber-50" : "border-stone-200 text-stone-700 bg-stone-50"} />
        <StatBadge label="Propres"  value={analysis.clause_count - flaggedCount} color="border-emerald-300/50 text-emerald-700 bg-emerald-50" />
      </div>

      {(allLabels.length > 0 || allFlags.length > 0) && (
        <div className="flex flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-stone-500">Label :</label>
            <select
              value={labelFilter}
              onChange={(e) => setLabelFilter(e.target.value)}
              className="rounded-md border border-stone-300 bg-white px-2 py-1 text-xs text-stone-700"
            >
              <option value="all">Tous</option>
              {allLabels.map((l) => (
                <option key={l} value={l}>{l.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-stone-500">Flag :</label>
            <select
              value={flagFilter}
              onChange={(e) => setFlagFilter(e.target.value)}
              className="rounded-md border border-stone-300 bg-white px-2 py-1 text-xs text-stone-700"
            >
              <option value="all">Tous</option>
              {allFlags.map((f) => (
                <option key={f} value={f}>{f.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          {(labelFilter !== "all" || flagFilter !== "all") && (
            <button
              type="button"
              onClick={() => { setLabelFilter("all"); setFlagFilter("all"); }}
              className="text-xs text-stone-500 hover:text-stone-700"
            >
              Réinitialiser
            </button>
          )}
          <span className="text-xs text-stone-500 self-center">
            {filtered.length} / {analysis.clause_count}
          </span>
        </div>
      )}

      <div className="space-y-3">
        {filtered.length === 0 ? (
          <p className="text-sm text-stone-500">Aucune clause ne correspond aux filtres sélectionnés.</p>
        ) : (
          filtered.map((clause) => (
            <ClauseCard key={clause.clause_id} clause={clause} />
          ))
        )}
      </div>
    </div>
  );
}
