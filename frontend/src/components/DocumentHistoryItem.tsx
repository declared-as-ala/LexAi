import type { DocumentBaseResponse } from "../types/documents";

const STATUS_CONFIG: Record<string, {
  label: string;
  dot: string;
  badge: string;
  accent: string;
  bar: string;
}> = {
  queued:       { label: "En attente",   dot: "bg-amber-500",                    badge: "bg-amber-50 text-amber-700 border-amber-300/50",    accent: "border-l-amber-400",   bar: "bg-amber-400" },
  extracting:   { label: "Extraction",   dot: "bg-sky-500 animate-pulse",        badge: "bg-sky-50 text-sky-700 border-sky-300/50",          accent: "border-l-sky-400",     bar: "bg-sky-400" },
  extracted:    { label: "Extrait",      dot: "bg-teal-500",                     badge: "bg-teal-50 text-teal-700 border-teal-300/50",       accent: "border-l-teal-400",    bar: "bg-teal-400" },
  analyzing:    { label: "Analyse NLP",  dot: "bg-violet-500 animate-pulse",     badge: "bg-violet-50 text-violet-700 border-violet-300/50", accent: "border-l-violet-400",  bar: "bg-violet-400" },
  analyzed:     { label: "Analysé",      dot: "bg-violet-500",                   badge: "bg-violet-50 text-violet-700 border-violet-300/50", accent: "border-l-violet-400",  bar: "bg-violet-400" },
  evaluating:   { label: "Évaluation",   dot: "bg-indigo-500 animate-pulse",     badge: "bg-indigo-50 text-indigo-700 border-indigo-300/50", accent: "border-l-indigo-400",  bar: "bg-indigo-400" },
  evaluated:    { label: "Évalué",       dot: "bg-indigo-500",                   badge: "bg-indigo-50 text-indigo-700 border-indigo-300/50", accent: "border-l-indigo-400",  bar: "bg-indigo-400" },
  recommending: { label: "Recommande",   dot: "bg-fuchsia-500 animate-pulse",    badge: "bg-fuchsia-50 text-fuchsia-700 border-fuchsia-300/50", accent: "border-l-fuchsia-400", bar: "bg-fuchsia-400" },
  complete:     { label: "Complet",      dot: "bg-emerald-500",                  badge: "bg-emerald-50 text-emerald-700 border-emerald-300/50", accent: "border-l-emerald-400", bar: "bg-emerald-400" },
  failed:       { label: "Échec",        dot: "bg-rose-500",                     badge: "bg-rose-50 text-rose-700 border-rose-300/50",       accent: "border-l-rose-400",    bar: "bg-rose-400" },
  uploaded:     { label: "Téléversé",    dot: "bg-stone-400",                    badge: "bg-stone-100 text-stone-600 border-stone-300/50",   accent: "border-l-stone-400",   bar: "bg-stone-400" },
};

function FileIcon({ mimeType }: { mimeType?: string }) {
  const isPdf = mimeType?.includes("pdf");
  const isDoc = mimeType?.includes("word") || mimeType?.includes("docx");
  const isImg = mimeType?.startsWith("image/");

  return (
    <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      {isImg ? (
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
      ) : isPdf ? (
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      ) : isDoc ? (
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      ) : (
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      )}
    </svg>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentHistoryItem({
  document,
  selected,
  onSelect,
  onDelete,
  deleting,
}: {
  document: DocumentBaseResponse;
  selected: boolean;
  onSelect: (id: number) => void;
  onDelete: (id: number) => void;
  deleting?: boolean;
}) {
  const cfg = STATUS_CONFIG[document.status] ?? STATUS_CONFIG.uploaded;
  const createdAt = document.created_at
    ? new Date(document.created_at).toLocaleString("fr-TN", { dateStyle: "short", timeStyle: "short" })
    : "—";
  const inProgress = ["queued", "extracting", "analyzing", "evaluating", "recommending"].includes(document.status);

  return (
    <div
      className={`group relative overflow-hidden rounded-xl border-l-[3px] border border-stone-200/80 transition-all duration-200 ${cfg.accent} ${
        selected
          ? "bg-gradient-to-br from-amber-50 via-stone-50 to-amber-50/60 shadow-md border-r-stone-200/80 border-t-stone-200/80 border-b-stone-200/80"
          : "bg-white/60 hover:border-stone-200 hover:bg-amber-50/30 hover:shadow-sm"
      }`}
    >
      <button
        type="button"
        onClick={() => onSelect(document.id)}
        className="w-full p-3.5 pl-4 text-left"
      >
        <div className="flex items-start gap-3">
          {/* File icon */}
          <div
            className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border transition-colors shadow-sm ${
              selected
                ? `${cfg.badge} border-current/30`
                : "border-stone-200 bg-white text-stone-500"
            }`}
          >
            <FileIcon mimeType={document.mime_type} />
          </div>

          {/* Content */}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold leading-tight text-stone-900">
              {document.filename}
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11px] text-stone-500">
              <span>{formatBytes(document.size_bytes)}</span>
              <span className="text-stone-300">·</span>
              <span>{createdAt}</span>
            </div>
          </div>

          {/* Status badge */}
          <span
            className={`shrink-0 flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${cfg.badge}`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
            {cfg.label}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mt-2.5 pl-0">
          <div className="h-1 overflow-hidden rounded-full bg-stone-200/80">
            <div
              className={`progress-bar-smooth h-full rounded-full ${cfg.bar}`}
              style={{ width: `${document.progress_percent}%` }}
            />
          </div>
          {inProgress && document.progress_message && (
            <p className="mt-1 truncate text-[10px] text-stone-500">
              {document.progress_message}
            </p>
          )}
        </div>
      </button>

      {/* Delete button */}
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); onDelete(document.id); }}
        disabled={deleting || inProgress}
        title={inProgress ? "Suppression impossible en cours de traitement" : "Supprimer"}
        className={`absolute right-2.5 top-2.5 rounded-lg p-1.5 transition-all duration-150
          ${deleting ? "opacity-50 cursor-not-allowed" : ""}
          ${inProgress ? "cursor-not-allowed opacity-0" : "opacity-0 group-hover:opacity-80"}
          text-stone-400 hover:bg-rose-50 hover:text-rose-600`}
      >
        {deleting ? (
          <svg className="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        ) : (
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        )}
      </button>
    </div>
  );
}
