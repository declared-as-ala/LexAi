import type {
  ClauseListResponse,
  DocumentListResponse,
  DocumentDetailResponse,
  DocumentSummaryResponse,
  EvaluationResponse,
  ExtractionResponse,
  NLPAnalysisResponse,
  RecommendationsListResponse,
  RetryDocumentResponse,
  RewriteFinalResponse,
  RewriteGenerateResponse,
  RewritesListResponse,
  UploadDocumentResponse,
} from "../types/documents";
import { apiRequest } from "./client";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function uploadDocument(file: File): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<UploadDocumentResponse>;
}

export function getDocument(id: number): Promise<DocumentDetailResponse> {
  return apiRequest<DocumentDetailResponse>(`/documents/${id}`);
}

export function getDocumentExtraction(id: number): Promise<ExtractionResponse> {
  return apiRequest<ExtractionResponse>(`/documents/${id}/extraction`);
}

export function listDocuments(limit = 50, offset = 0): Promise<DocumentListResponse> {
  return apiRequest<DocumentListResponse>(`/documents?limit=${limit}&offset=${offset}`);
}

export function getDocumentSummary(): Promise<DocumentSummaryResponse> {
  return apiRequest<DocumentSummaryResponse>("/documents/summary");
}

export async function retryDocumentExtraction(id: number): Promise<RetryDocumentResponse> {
  return apiRequest<RetryDocumentResponse>(`/documents/${id}/retry`, {
    method: "POST",
  });
}

export async function deleteDocument(id: number): Promise<void> {
  await apiRequest<void>(`/documents/${id}`, {
    method: "DELETE",
  });
}

export function getDocumentAnalysis(id: number): Promise<NLPAnalysisResponse> {
  return apiRequest<NLPAnalysisResponse>(`/documents/${id}/analysis`);
}

export function getDocumentClauses(id: number, label?: string, flag?: string): Promise<ClauseListResponse> {
  const params = new URLSearchParams({ limit: "100" });
  if (label) params.set("label", label);
  if (flag) params.set("flag", flag);
  return apiRequest<ClauseListResponse>(`/documents/${id}/clauses?${params.toString()}`);
}

export function getDocumentEvaluation(id: number): Promise<EvaluationResponse> {
  return apiRequest<EvaluationResponse>(`/documents/${id}/evaluation`);
}

export function getDocumentRecommendations(id: number): Promise<RecommendationsListResponse> {
  return apiRequest<RecommendationsListResponse>(`/documents/${id}/recommendations`);
}

export function getDocumentRewrites(id: number): Promise<RewritesListResponse> {
  return apiRequest<RewritesListResponse>(`/documents/${id}/rewrites`);
}

export async function postRewriteAccept(
  documentId: number,
  clauseId: string,
  recommendationId?: number,
): Promise<void> {
  await apiRequest(`/documents/${documentId}/rewrites/${encodeURIComponent(clauseId)}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recommendation_id: recommendationId ?? null }),
  });
}

export async function postRewriteReject(
  documentId: number,
  clauseId: string,
  recommendationId?: number,
): Promise<void> {
  await apiRequest(`/documents/${documentId}/rewrites/${encodeURIComponent(clauseId)}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recommendation_id: recommendationId ?? null }),
  });
}

export async function postRewriteKeepOriginal(
  documentId: number,
  clauseId: string,
  recommendationId?: number,
): Promise<void> {
  await apiRequest(`/documents/${documentId}/rewrites/${encodeURIComponent(clauseId)}/keep-original`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recommendation_id: recommendationId ?? null }),
  });
}

export function postRewriteGenerate(documentId: number): Promise<RewriteGenerateResponse> {
  return apiRequest<RewriteGenerateResponse>(`/documents/${documentId}/rewrites/generate`, {
    method: "POST",
  });
}

export function getRewriteFinal(documentId: number): Promise<RewriteFinalResponse> {
  return apiRequest<RewriteFinalResponse>(`/documents/${documentId}/rewrites/final`);
}

async function postExportBlob(documentId: number, kind: "docx" | "pdf", sessionId?: number): Promise<Blob> {
  const q = sessionId != null ? `?session_id=${sessionId}` : "";
  const response = await fetch(`${API_BASE}/documents/${documentId}/exports/${kind}${q}`, { method: "POST" });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.blob();
}

export function downloadRevisedDocx(documentId: number, sessionId?: number): Promise<Blob> {
  return postExportBlob(documentId, "docx", sessionId);
}

export function downloadRevisedPdf(documentId: number, sessionId?: number): Promise<Blob> {
  return postExportBlob(documentId, "pdf", sessionId);
}

