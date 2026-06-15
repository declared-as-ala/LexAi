import { useCallback, useEffect, useState } from "react";

import {
  downloadRevisedDocx,
  downloadRevisedPdf,
  getRewriteFinal,
  postRewriteAccept,
  postRewriteGenerate,
  postRewriteKeepOriginal,
  postRewriteReject,
} from "../api/documents";
import type { RewriteDecisionItem, RewriteFinalResponse, RewritesListResponse } from "../types/documents";

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-rose-50 text-rose-700 border-rose-300/50",
  high:     "bg-orange-50 text-orange-700 border-orange-300/50",
  medium:   "bg-amber-50 text-amber-700 border-amber-300/50",
  low:      "bg-stone-100 text-stone-600 border-stone-300/50",
};

const DECISION_LABEL: Record<string, string> = {
  pending:       "En attente",
  accepted:      "Réécriture acceptée",
  rejected:      "Réécriture refusée",
  keep_original: "Texte d'origine conservé",
};

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function RewriteReviewPanel({
  documentId,
  data,
  loadError,
  onRefresh,
}: {
  documentId: number;
  data: RewritesListResponse | null;
  loadError: string | null;
  onRefresh: () => Promise<void>;
}) {
  const [busy, setBusy] = useState<number | null>(null);
  const [generateBusy, setGenerateBusy] = useState(false);
  const [exportBusy, setExportBusy] = useState<"docx" | "pdf" | null>(null);
  const [finalData, setFinalData] = useState<RewriteFinalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshFinal = useCallback(async () => {
    try {
      const f = await getRewriteFinal(documentId);
      setFinalData(f);
    } catch {
      setFinalData(null);
    }
  }, [documentId]);

  useEffect(() => {
    void refreshFinal();
  }, [refreshFinal]);

  const handleDecision = async (item: RewriteDecisionItem, action: "accept" | "reject" | "keep") => {
    const cid = item.clause_id;
    if (!cid) {
      setError("Cette recommandation n'est pas liée à une clause segmentée.");
      return;
    }
    setBusy(item.recommendation_id);
    setError(null);
    try {
      if (action === "accept") {
        await postRewriteAccept(documentId, cid, item.recommendation_id);
      } else if (action === "reject") {
        await postRewriteReject(documentId, cid, item.recommendation_id);
      } else {
        await postRewriteKeepOriginal(documentId, cid, item.recommendation_id);
      }
      await onRefresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action impossible");
    } finally {
      setBusy(null);
    }
  };

  const handleGenerate = async () => {
    setGenerateBusy(true);
    setError(null);
    try {
      await postRewriteGenerate(documentId);
      await onRefresh();
      await refreshFinal();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Génération impossible");
    } finally {
      setGenerateBusy(false);
    }
  };

  const handleExport = async (kind: "docx" | "pdf") => {
    setExportBusy(kind);
    setError(null);
    try {
      const sid = finalData?.session_id;
      const blob =
        kind === "docx" ? await downloadRevisedDocx(documentId, sid) : await downloadRevisedPdf(documentId, sid);
      triggerDownload(blob, `revised_${documentId}.${kind === "docx" ? "docx" : "pdf"}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export impossible");
    } finally {
      setExportBusy(null);
    }
  };

  if (loadError) {
    return (
      <div className="lex-panel p-6 sm:p-7">
        <p className="text-sm text-rose-700">{loadError}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="lex-panel p-6 sm:p-7">
        <p className="text-sm text-stone-500">Chargement de la session de réécriture…</p>
      </div>
    );
  }

  const actionable = data.items.filter((i) => i.clause_id && (i.rewritten_clause || "").trim().length > 0);

  return (
    <div className="lex-panel p-6 sm:p-7 ring-1 ring-teal-300/20">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-teal-700">Réécriture</p>
          <h2 className="font-display mt-1 text-xl font-medium text-stone-900">Revue des clauses et export</h2>
          <p className="mt-1 max-w-2xl text-sm text-stone-500">
            Session #{data.session.id} · {data.session.status === "draft" ? "Brouillon" : "Finalisée"} — acceptez les
            réécritures proposées par l'agent 4, puis générez le contrat révisé.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void handleGenerate()}
            disabled={generateBusy}
            className="rounded-xl border border-teal-400/50 bg-teal-50 px-4 py-2.5 text-sm font-semibold text-teal-700 shadow-sm transition hover:bg-teal-100 disabled:opacity-50"
          >
            {generateBusy ? "Génération…" : "Générer le contrat révisé"}
          </button>
          <button
            type="button"
            onClick={() => void handleExport("docx")}
            disabled={exportBusy !== null}
            className="rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-sm font-semibold text-stone-700 shadow-sm transition hover:bg-stone-50 disabled:opacity-50"
          >
            {exportBusy === "docx" ? "DOCX…" : "DOCX"}
          </button>
          <button
            type="button"
            onClick={() => void handleExport("pdf")}
            disabled={exportBusy !== null}
            className="rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-sm font-semibold text-stone-700 shadow-sm transition hover:bg-stone-50 disabled:opacity-50"
          >
            {exportBusy === "pdf" ? "PDF…" : "PDF"}
          </button>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-xl border border-rose-300/50 bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          {error}
        </div>
      )}

      {finalData && (
        <div className="mt-5 rounded-xl border border-stone-200 bg-stone-50 p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-500">Dernière version finalisée</p>
          <p className="mt-1 text-xs text-stone-500">
            Session export #{finalData.session_id} · {finalData.final_text.length} caractères
          </p>
          <pre className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap rounded-lg border border-stone-200 bg-white p-3 text-xs text-stone-700 font-mono">
            {finalData.final_text.slice(0, 4000)}
            {finalData.final_text.length > 4000 ? "\n…" : ""}
          </pre>
        </div>
      )}

      <div className="mt-6 space-y-4">
        {actionable.length === 0 ? (
          <p className="text-sm text-stone-500">
            Aucune réécriture de clause proposée pour ce document. Les exports reprendront le texte normalisé inchangé
            après génération.
          </p>
        ) : (
          actionable.map((item) => {
            const sev = (item.severity || "medium").toLowerCase();
            const badge = SEVERITY_BADGE[sev] ?? SEVERITY_BADGE.medium;
            const dlabel = DECISION_LABEL[item.decision] ?? item.decision;
            return (
              <div
                key={item.recommendation_id}
                className="overflow-hidden rounded-xl border border-stone-200 bg-white/80 shadow-sm"
              >
                <div className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0 flex-1 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-semibold uppercase tracking-wide text-teal-700">
                        {item.framework || "—"}
                        {item.article ? ` · ${item.article}` : ""}
                      </span>
                      <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase ${badge}`}>
                        {item.severity || "—"}
                      </span>
                      <span className="rounded border border-stone-300/50 bg-stone-100 px-1.5 py-0.5 text-[10px] text-stone-600">
                        {dlabel}
                      </span>
                    </div>
                    {item.compliance_flags.length > 0 && (
                      <p className="text-[11px] text-amber-700">Flags : {item.compliance_flags.join(", ")}</p>
                    )}
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-500">Clause d'origine</p>
                      <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap rounded-lg border border-stone-200 bg-stone-100 p-2 text-xs text-stone-700 font-mono">
                        {item.original_clause_text || "—"}
                      </pre>
                    </div>
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-500">Réécriture suggérée</p>
                      <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap rounded-lg border border-teal-200 bg-teal-50 p-2 text-xs text-teal-800 font-mono">
                        {item.rewritten_clause}
                      </pre>
                    </div>
                    {item.legal_rationale && (
                      <p className="text-xs leading-relaxed text-stone-500">{item.legal_rationale}</p>
                    )}
                  </div>
                  <div className="flex shrink-0 flex-wrap gap-2 sm:flex-col">
                    <button
                      type="button"
                      disabled={busy === item.recommendation_id}
                      onClick={() => void handleDecision(item, "accept")}
                      className="rounded-lg border border-teal-400/50 bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-700 hover:bg-teal-100 disabled:opacity-50"
                    >
                      Accepter
                    </button>
                    <button
                      type="button"
                      disabled={busy === item.recommendation_id}
                      onClick={() => void handleDecision(item, "reject")}
                      className="rounded-lg border border-rose-300/50 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 disabled:opacity-50"
                    >
                      Refuser
                    </button>
                    <button
                      type="button"
                      disabled={busy === item.recommendation_id}
                      onClick={() => void handleDecision(item, "keep")}
                      className="rounded-lg border border-stone-300 bg-stone-100 px-3 py-1.5 text-xs font-semibold text-stone-600 hover:bg-stone-200 disabled:opacity-50"
                    >
                      Garder l'original
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
