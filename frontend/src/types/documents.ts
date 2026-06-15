export type DocumentStatus =
  | "uploaded"
  | "queued"
  | "extracting"
  | "extracted"
  | "analyzing"
  | "analyzed"
  | "evaluating"
  | "evaluated"
  | "recommending"
  | "complete"
  | "failed";

export type ProgressStage =
  | "queued"
  | "starting"
  | "selecting_provider"
  | "extracting"
  | "normalizing"
  | "persisting"
  | "completed"
  | "failed"
  | "analyzing"
  | "segmenting"
  | "classifying"
  | "nlp_persisting"
  | "nlp_completed"
  | "evaluating"
  | "eval_rules"
  | "eval_scoring"
  | "eval_persisting"
  | "eval_completed"
  | "recommending"
  | "rec_templates"
  | "rec_llm"
  | "rec_persisting"
  | "rec_completed";

export interface UploadDocumentResponse {
  id: number;
  filename: string;
  status: DocumentStatus;
  progress_percent: number;
  progress_stage: ProgressStage;
  progress_message?: string | null;
}

export interface DocumentBaseResponse {
  id: number;
  name: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  status: DocumentStatus;
  progress_percent: number;
  progress_stage: ProgressStage;
  progress_message?: string | null;
  last_error?: string | null;
  task_id?: string | null;
  created_at: string | null;
  updated_at: string | null;
  finished_at?: string | null;
}

export interface DocumentDetailResponse extends DocumentBaseResponse {}

export interface DocumentListResponse {
  items: DocumentBaseResponse[];
  total_count: number;
}

export interface DocumentSummaryResponse {
  queued_count: number;
  extracting_count: number;
  extracted_count: number;
  analyzing_count: number;
  analyzed_count: number;
  evaluating_count: number;
  evaluated_count: number;
  recommending_count: number;
  complete_count: number;
  failed_count: number;
  total_count: number;
  agent1_success_rate: number;
  agent2_success_rate: number;
  agent3_success_rate: number;
  agent4_success_rate: number;
}

// ── Agent 2 NLP Analysis types ────────────────────────────────────────────────

export interface EntitySchema {
  text: string;
  label: string;
  start: number;
  end: number;
  confidence: number;
  source: string;
}

export interface ClauseAnalysis {
  clause_id: string;
  text: string;
  start_char: number;
  end_char: number;
  section_title: string | null;
  source: string;
  labels: string[];
  compliance_flags: string[];
  entities: EntitySchema[];
  confidence: number;
  model_used: string;
}

export interface NLPAnalysisResponse {
  document_id: number;
  analysis_id: number;
  language: string | null;
  language_confidence: number | null;
  clause_count: number;
  risk_level: "low" | "medium" | "high" | "critical" | null;
  compliance_score: number | null;
  model_used: string | null;
  created_at: string;
  clauses: ClauseAnalysis[];
}

export interface ClauseListResponse {
  document_id: number;
  total_count: number;
  items: ClauseAnalysis[];
}

// ── Agent 3 Evaluation types ─────────────────────────────────────────────────

export interface ViolationSchema {
  violation_id: string;
  rule_id: string;
  framework: string;
  article: string;
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low";
  clause_id: string | null;
  clause_text: string | null;
  remediation_hint: string;
}

export interface EvaluationResponse {
  document_id: number;
  evaluation_id: number;
  global_score: number | null;
  litigation_risk: "low" | "medium" | "high" | "critical" | null;
  framework_scores: Record<string, number>;
  framework_violation_counts: Record<string, number>;
  active_frameworks: string[];
  violations: ViolationSchema[];
  missing_clauses: string[];
  violation_count: number;
  evaluated_at: string | null;
  created_at: string;
}

// ── Agent 4 Recommendation types ─────────────────────────────────────────────

export interface RecommendationItem {
  id: number;
  priority: number | null;
  framework: string | null;
  article: string | null;
  severity: string | null;
  clause_id: string | null;
  violation_id: string | null;
  violation_rule_id: string | null;
  issue_description: string | null;
  recommendation_text: string | null;
  rewritten_clause: string | null;
  legal_rationale: string | null;
  generated_by: string | null;
  created_at: string;
}

export interface RecommendationsListResponse {
  document_id: number;
  total: number;
  recommendations: RecommendationItem[];
}

// ── Contract rewrite (post–Agent 4) ─────────────────────────────────────────

export interface RewriteSessionSummary {
  id: number;
  document_id: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface RewriteDecisionItem {
  recommendation_id: number;
  clause_id: string | null;
  decision: string;
  rewritten_clause: string | null;
  issue_description: string | null;
  severity: string | null;
  priority: number | null;
  framework: string | null;
  article: string | null;
  legal_rationale: string | null;
  original_clause_text: string | null;
  compliance_flags: string[];
}

export interface RewritesListResponse {
  document_id: number;
  session: RewriteSessionSummary;
  items: RewriteDecisionItem[];
}

export interface RewriteGenerateResponse {
  document_id: number;
  session_id: number;
  status: string;
  final_text_length: number;
  changed_clauses: number;
  message: string;
}

export interface RewriteFinalResponse {
  document_id: number;
  session_id: number;
  final_text: string;
  revision_metadata: Array<Record<string, unknown>>;
  exports: Array<Record<string, unknown>>;
}

export interface RetryDocumentResponse {
  id: number;
  status: DocumentStatus;
  progress_percent: number;
  progress_stage: ProgressStage;
  progress_message?: string | null;
}

export interface DocumentMetadata {
  filename: string;
  mime_type: string;
  size_bytes: number;
  page_count?: number | null;
}

export interface ExtractionPayload {
  document_metadata: DocumentMetadata;
  raw_text: string;
  normalized_text: string;
  structure?: Record<string, unknown> | null;
  page_metadata?: Array<Record<string, unknown>> | null;
  warnings: string[];
  errors: string[];
}

export interface ExtractionResponse {
  document_id: number;
  extraction: ExtractionPayload | null;
  message?: string | null;
}
