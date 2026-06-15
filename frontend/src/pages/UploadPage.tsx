import { useCallback, useEffect, useMemo, useState } from "react";

import { getHealth } from "../api/client";
import {
  getDocument,
  getDocumentAnalysis,
  getDocumentEvaluation,
  getDocumentExtraction,
  getDocumentRecommendations,
  getDocumentRewrites,
  getDocumentSummary,
  listDocuments,
  retryDocumentExtraction,
  deleteDocument as apiDeleteDocument,
  uploadDocument,
} from "../api/documents";
import { AnalysisViewer } from "../components/AnalysisViewer";
import { DocumentHistoryList } from "../components/DocumentHistoryList";
import { DocumentStatusCard } from "../components/DocumentStatusCard";
import { EmptyWorkspaceState } from "../components/EmptyWorkspaceState";
import { EvaluationViewer } from "../components/EvaluationViewer";
import { AgentPipeline } from "../components/AgentPipeline";
import { RecommendationViewer } from "../components/RecommendationViewer";
import { RewriteReviewPanel } from "../components/RewriteReviewPanel";
import { ExtractionViewer } from "../components/ExtractionViewer";
import { FailedExtractionState } from "../components/FailedExtractionState";
import { ProgressCard } from "../components/ProgressCard";
import { QueueSummaryCards } from "../components/QueueSummaryCards";
import { UploadDropzone } from "../components/UploadDropzone";
import type {
  DocumentBaseResponse,
  DocumentDetailResponse,
  DocumentSummaryResponse,
  EvaluationResponse,
  ExtractionResponse,
  NLPAnalysisResponse,
  RecommendationsListResponse,
  RewritesListResponse,
} from "../types/documents";

const STORAGE_KEY = "agent1:selectedDocumentId";
const IN_PROGRESS = ["queued", "extracting", "analyzing", "evaluating", "recommending"];
const PIPELINE_UI_STATUSES = ["analyzed", "evaluating", "evaluated", "recommending", "complete"];
const RECOMMENDATION_FETCH_STATUSES = ["evaluated", "recommending", "complete"];
const REWRITE_UI_STATUSES = ["evaluated", "complete"];

const UPLOAD_ALLOWED_EXTENSIONS = new Set([
  ".pdf", ".doc", ".docx", ".txt", ".html", ".htm",
  ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp",
]);

export function UploadPage() {
  const [documents, setDocuments] = useState<DocumentBaseResponse[]>([]);
  const [summary, setSummary] = useState<DocumentSummaryResponse | null>(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetailResponse | null>(null);
  const [selectedExtraction, setSelectedExtraction] = useState<ExtractionResponse | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<NLPAnalysisResponse | null>(null);
  const [selectedEvaluation, setSelectedEvaluation] = useState<EvaluationResponse | null>(null);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
  const [selectedRecommendations, setSelectedRecommendations] = useState<RecommendationsListResponse | null>(null);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const [rewritesData, setRewritesData] = useState<RewritesListResponse | null>(null);
  const [rewriteError, setRewriteError] = useState<string | null>(null);
  const [agent4LlmEnabled, setAgent4LlmEnabled] = useState<boolean | null>(null);
  const [imageOcrSupported, setImageOcrSupported] = useState<boolean | null>(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [loadingWorkspace, setLoadingWorkspace] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const shouldPoll = useMemo(
    () =>
      documents.some((d) => IN_PROGRESS.includes(d.status)) ||
      (selectedDocument?.status != null && IN_PROGRESS.includes(selectedDocument.status)),
    [documents, selectedDocument?.status],
  );

  const fetchRewrites = useCallback(async (documentId: number, status: string) => {
    if (!REWRITE_UI_STATUSES.includes(status)) {
      setRewritesData(null);
      setRewriteError(null);
      return;
    }
    try {
      const rw = await getDocumentRewrites(documentId);
      setRewritesData(rw);
      setRewriteError(null);
    } catch (e) {
      setRewritesData(null);
      setRewriteError(e instanceof Error ? e.message : "Échec du chargement des réécritures.");
    }
  }, []);

  const refreshWorkspace = useCallback(async (preferredId?: number | null) => {
    const [listResponse, summaryResponse] = await Promise.all([listDocuments(), getDocumentSummary()]);
    setDocuments(listResponse.items);
    setSummary(summaryResponse);
    setSelectedDocumentId((current) => {
      const storedId = preferredId ?? current ?? Number(window.localStorage.getItem(STORAGE_KEY));
      if (storedId && listResponse.items.some((item) => item.id === storedId)) return storedId;
      return listResponse.items[0]?.id ?? null;
    });
  }, []);

  const refreshSelectedDocument = useCallback(async (documentId: number) => {
    const [documentResponse, extractionResponse] = await Promise.all([
      getDocument(documentId),
      getDocumentExtraction(documentId),
    ]);
    setSelectedDocument(documentResponse);
    setSelectedExtraction(extractionResponse);
    if (PIPELINE_UI_STATUSES.includes(documentResponse.status)) {
      try {
        const analysisResponse = await getDocumentAnalysis(documentId);
        setSelectedAnalysis(analysisResponse);
      } catch {
        setSelectedAnalysis(null);
      }
    } else {
      setSelectedAnalysis(null);
    }
    if (PIPELINE_UI_STATUSES.includes(documentResponse.status)) {
      try {
        const evalResponse = await getDocumentEvaluation(documentId);
        setSelectedEvaluation(evalResponse);
        setEvaluationError(null);
      } catch (e) {
        setSelectedEvaluation(null);
        setEvaluationError(e instanceof Error ? e.message : "Failed to load Agent 3 evaluation.");
      }
    } else {
      setSelectedEvaluation(null);
      setEvaluationError(null);
    }
    if (RECOMMENDATION_FETCH_STATUSES.includes(documentResponse.status)) {
      try {
        const recResponse = await getDocumentRecommendations(documentId);
        setSelectedRecommendations(recResponse);
        setRecommendationError(null);
      } catch (e) {
        setSelectedRecommendations(null);
        setRecommendationError(e instanceof Error ? e.message : "Failed to load Agent 4 recommendations.");
      }
    } else {
      setSelectedRecommendations(null);
      setRecommendationError(null);
    }
    await fetchRewrites(documentId, documentResponse.status);
  }, [fetchRewrites]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        await refreshWorkspace();
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        if (active) setLoadingWorkspace(false);
      }
    })();
    return () => { active = false; };
  }, [refreshWorkspace]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const h = await getHealth();
        if (!active) return;
        setAgent4LlmEnabled(Boolean(h.agent4_llm_enabled));
        if (typeof h.image_ocr_upload === "boolean") {
          setImageOcrSupported(h.image_ocr_upload);
        }
      } catch {
        if (active) {
          setAgent4LlmEnabled(null);
          setImageOcrSupported(null);
        }
      }
    })();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (selectedDocumentId == null) {
      setSelectedDocument(null);
      setSelectedExtraction(null);
      setSelectedAnalysis(null);
      setSelectedEvaluation(null);
      setEvaluationError(null);
      setSelectedRecommendations(null);
      setRecommendationError(null);
      setRewritesData(null);
      setRewriteError(null);
      window.localStorage.removeItem(STORAGE_KEY);
      return;
    }
    window.localStorage.setItem(STORAGE_KEY, String(selectedDocumentId));
    let active = true;
    (async () => {
      try {
        const [doc, ext] = await Promise.all([
          getDocument(selectedDocumentId),
          getDocumentExtraction(selectedDocumentId),
        ]);
        if (!active) return;
        setSelectedDocument(doc);
        setSelectedExtraction(ext);
        if (PIPELINE_UI_STATUSES.includes(doc.status)) {
          try {
            const analysis = await getDocumentAnalysis(selectedDocumentId);
            if (active) setSelectedAnalysis(analysis);
          } catch {
            if (active) setSelectedAnalysis(null);
          }
        } else {
          if (active) setSelectedAnalysis(null);
        }
        if (PIPELINE_UI_STATUSES.includes(doc.status)) {
          try {
            const evaluation = await getDocumentEvaluation(selectedDocumentId);
            if (active) setSelectedEvaluation(evaluation);
            if (active) setEvaluationError(null);
          } catch (e) {
            if (active) setSelectedEvaluation(null);
            if (active) setEvaluationError(e instanceof Error ? e.message : "Failed to load Agent 3 evaluation.");
          }
        } else {
          if (active) setSelectedEvaluation(null);
          if (active) setEvaluationError(null);
        }
        if (RECOMMENDATION_FETCH_STATUSES.includes(doc.status)) {
          try {
            const recs = await getDocumentRecommendations(selectedDocumentId);
            if (active) setSelectedRecommendations(recs);
            if (active) setRecommendationError(null);
          } catch (e) {
            if (active) setSelectedRecommendations(null);
            if (active) setRecommendationError(e instanceof Error ? e.message : "Failed to load Agent 4 recommendations.");
          }
        } else {
          if (active) setSelectedRecommendations(null);
          if (active) setRecommendationError(null);
        }
        if (active) await fetchRewrites(selectedDocumentId, doc.status);
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : "Unknown error");
      }
    })();
    return () => { active = false; };
  }, [selectedDocumentId, fetchRewrites]);

  useEffect(() => {
    if (!shouldPoll) return;
    const timer = window.setInterval(async () => {
      try {
        await refreshWorkspace(selectedDocumentId);
        if (selectedDocumentId != null) await refreshSelectedDocument(selectedDocumentId);
      } catch { /* keep existing state on poll failure */ }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [refreshSelectedDocument, refreshWorkspace, selectedDocumentId, shouldPoll]);

  const handleFilesSelect = async (files: File[]) => {
    setError(null);
    for (const file of files) {
      const dot = file.name.lastIndexOf(".");
      const ext = dot >= 0 ? file.name.slice(dot).toLowerCase() : "";
      if (!UPLOAD_ALLOWED_EXTENSIONS.has(ext)) {
        setError(`Type de fichier non supporté (${ext || "sans extension"}) : ${file.name}`);
        return;
      }
    }
    setUploading(true);
    let lastId: number | null = null;
    try {
      for (const file of files) {
        const res = await uploadDocument(file);
        lastId = res.id;
      }
      await refreshWorkspace(lastId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Téléversement échoué");
    } finally {
      setUploading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      await refreshWorkspace(selectedDocumentId);
      if (selectedDocumentId != null) await refreshSelectedDocument(selectedDocumentId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Actualisation échouée");
    } finally {
      setRefreshing(false);
    }
  };

  const handleRetry = async () => {
    if (selectedDocumentId == null) return;
    setRetrying(true);
    setError(null);
    try {
      await retryDocumentExtraction(selectedDocumentId);
      await refreshWorkspace(selectedDocumentId);
      await refreshSelectedDocument(selectedDocumentId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Relance échouée");
    } finally {
      setRetrying(false);
    }
  };

  const handleDelete = async (documentId: number) => {
    const doc = documents.find((d) => d.id === documentId);
    if (!doc) return;
    if (IN_PROGRESS.includes(doc.status)) {
      setError("Impossible de supprimer un document en cours de traitement.");
      return;
    }
    setDeletingId(documentId);
    setError(null);
    try {
      await apiDeleteDocument(documentId);
      if (documentId === selectedDocumentId) {
        setSelectedDocument(null);
        setSelectedExtraction(null);
        setSelectedAnalysis(null);
        setSelectedEvaluation(null);
        setEvaluationError(null);
        setSelectedRecommendations(null);
        setRecommendationError(null);
      }
      await refreshWorkspace();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Suppression échouée");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden text-stone-900">
      {/* Background layers */}
      <div className="pointer-events-none fixed inset-0 lex-glow-hero" aria-hidden />
      <div className="pointer-events-none fixed inset-0 lex-grid-bg opacity-60" aria-hidden />

      <div className="relative mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8 lg:py-10">

        {/* ── Header ── */}
        <header className="lex-panel animate-slide-up overflow-hidden">
          {/* Gold accent bar at top */}
          <div className="h-1 w-full bg-gradient-to-r from-gold-600 via-gold-400 to-gold-300" />

          <div className="p-6 sm:p-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0 max-w-2xl">
                {/* Brand */}
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-gold-500 to-gold-400 shadow-[0_4px_16px_rgba(201,163,54,0.40)]">
                    <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.97z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-gold-600">LexAI</p>
                    <h1 className="lex-title -mt-0.5 text-xl font-semibold text-stone-900 sm:text-2xl">
                      Compliance Command Center
                    </h1>
                  </div>
                </div>

                <p className="mt-3 max-w-lg text-sm leading-relaxed text-stone-500">
                  Pipeline IA complet : extraction documentaire, analyse NLP des clauses,
                  évaluation de conformité{" "}
                  <span className="font-medium text-stone-700">LNPDP · RGPD · ISO 27001</span>,
                  et recommandations de remédiation.
                </p>

                {/* Legal framework badges */}
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {["LNPDP 2004-63", "RGPD EU 2016/679", "ISO 27001:2022", "ISO 9001:2015"].map((fw) => (
                    <span key={fw} className="rounded-full border border-gold-300/50 bg-amber-50 px-2.5 py-0.5 text-[10px] font-semibold text-gold-700">
                      {fw}
                    </span>
                  ))}
                </div>
              </div>

              {/* Refresh button */}
              <button
                type="button"
                onClick={handleRefresh}
                disabled={refreshing}
                className="group inline-flex shrink-0 items-center justify-center gap-2 self-start rounded-xl border border-gold-300/50 bg-white px-5 py-2.5 text-sm font-semibold text-stone-700 shadow-sm transition-all duration-200 hover:border-gold-400/70 hover:bg-amber-50 hover:text-gold-800 disabled:opacity-50"
              >
                <svg
                  className={`h-4 w-4 text-gold-500 transition-transform duration-500 ${refreshing ? "animate-spin" : "group-hover:rotate-180"}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
                {refreshing ? "Synchronisation…" : "Actualiser"}
              </button>
            </div>

            {/* Pipeline */}
            <div className="mt-6 border-t border-gold-200/40 pt-6">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-stone-400">
                Pipeline en direct
              </p>
              <div className="mt-4">
                <AgentPipeline status={selectedDocument?.status} />
              </div>
            </div>
          </div>
        </header>

        {/* ── Error banner ── */}
        {error && (
          <div
            role="alert"
            className="animate-slide-up flex items-start gap-3 rounded-xl border border-rose-300/50 bg-rose-50 px-4 py-3.5"
          >
            <svg className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <p className="flex-1 text-sm leading-relaxed text-rose-800">{error}</p>
            <button
              type="button"
              onClick={() => setError(null)}
              className="shrink-0 rounded-lg p-1 text-rose-400 transition hover:bg-rose-100 hover:text-rose-600"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* ── Main grid ── */}
        <div className="grid gap-6 xl:grid-cols-[minmax(0,360px)_minmax(0,1fr)] xl:items-start">

          {/* ── Left sidebar ── */}
          <aside className="flex flex-col gap-4">
            <UploadDropzone
              onFilesSelect={handleFilesSelect}
              loading={uploading}
              agent4LlmEnabled={agent4LlmEnabled}
              imageOcrSupported={imageOcrSupported}
            />
            <QueueSummaryCards summary={summary} />
            <DocumentHistoryList
              documents={documents}
              selectedDocumentId={selectedDocumentId}
              onSelect={setSelectedDocumentId}
              onDelete={handleDelete}
              deletingId={deletingId}
              loading={loadingWorkspace}
            />
          </aside>

          {/* ── Right content ── */}
          <section className="flex min-w-0 flex-col gap-4">
            {documents.length === 0 && !loadingWorkspace ? (
              <EmptyWorkspaceState />
            ) : (
              <>
                <DocumentStatusCard document={selectedDocument} />
                <ProgressCard document={selectedDocument} />

                {selectedDocument?.status === "failed" ? (
                  <FailedExtractionState
                    error={selectedDocument.last_error}
                    onRetry={handleRetry}
                    retrying={retrying}
                  />
                ) : (
                  <>
                    <ExtractionViewer extraction={selectedExtraction} document={selectedDocument} />

                    {PIPELINE_UI_STATUSES.includes(selectedDocument?.status ?? "") && (
                      <AnalysisViewer analysis={selectedAnalysis} />
                    )}

                    {evaluationError && (
                      <div
                        role="status"
                        className="rounded-xl border border-amber-300/50 bg-amber-50 px-4 py-3 text-sm text-amber-800"
                      >
                        Évaluation Agent 3 non disponible : {evaluationError}
                      </div>
                    )}

                    {selectedEvaluation && (
                      <EvaluationViewer evaluation={selectedEvaluation} />
                    )}

                    {recommendationError && RECOMMENDATION_FETCH_STATUSES.includes(selectedDocument?.status ?? "") && (
                      <div
                        role="status"
                        className="rounded-xl border border-amber-300/50 bg-amber-50 px-4 py-3 text-sm text-amber-800"
                      >
                        Recommandations Agent 4 : {recommendationError}
                      </div>
                    )}

                    {selectedDocument != null && RECOMMENDATION_FETCH_STATUSES.includes(selectedDocument.status) && (
                      <RecommendationViewer
                        documentId={selectedDocument.id}
                        status={selectedDocument.status}
                        agent4LlmEnabled={agent4LlmEnabled}
                        data={
                          selectedRecommendations ?? {
                            document_id: selectedDocument.id,
                            total: 0,
                            recommendations: [],
                          }
                        }
                      />
                    )}

                    {selectedDocument != null && REWRITE_UI_STATUSES.includes(selectedDocument.status) && (
                      <RewriteReviewPanel
                        documentId={selectedDocument.id}
                        data={rewritesData}
                        loadError={rewriteError}
                        onRefresh={async () => {
                          await fetchRewrites(selectedDocument.id, selectedDocument.status);
                        }}
                      />
                    )}
                  </>
                )}
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
