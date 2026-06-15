import type { DocumentDetailResponse } from "../types/documents";

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  uploaded:     { label: "Uploaded",    color: "text-stone-600",   bg: "bg-stone-100 border border-stone-300/50" },
  queued:       { label: "Queued",      color: "text-amber-700",   bg: "bg-amber-50 border border-amber-300/50" },
  extracting:   { label: "Extracting",  color: "text-sky-700",     bg: "bg-sky-50 border border-sky-300/50" },
  extracted:    { label: "Extracted",   color: "text-teal-700",    bg: "bg-teal-50 border border-teal-300/50" },
  analyzing:    { label: "Analyzing",   color: "text-violet-700",  bg: "bg-violet-50 border border-violet-300/50" },
  analyzed:     { label: "Analyzed",    color: "text-violet-700",  bg: "bg-violet-50 border border-violet-300/50" },
  evaluating:   { label: "Evaluating",  color: "text-indigo-700",  bg: "bg-indigo-50 border border-indigo-300/50" },
  evaluated:    { label: "Evaluated",   color: "text-indigo-700",  bg: "bg-indigo-50 border border-indigo-300/50" },
  recommending: { label: "Recommending",color: "text-fuchsia-700", bg: "bg-fuchsia-50 border border-fuchsia-300/50" },
  complete:     { label: "Complete",    color: "text-emerald-700", bg: "bg-emerald-50 border border-emerald-300/50" },
  failed:       { label: "Failed",      color: "text-rose-700",    bg: "bg-rose-50 border border-rose-300/50" },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-widest text-stone-400">{label}</p>
      <p className="mt-0.5 text-sm text-stone-800 truncate">{value}</p>
    </div>
  );
}

export function DocumentStatusCard({ document }: { document: DocumentDetailResponse | null }) {
  if (!document) return null;

  const cfg = STATUS_CONFIG[document.status] ?? STATUS_CONFIG.uploaded;

  return (
    <div className="lex-panel p-5 sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">Fichier actif</p>
          <h2 className="font-display mt-1.5 truncate text-lg font-medium text-stone-900">{document.filename}</h2>
        </div>
        <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${cfg.bg} ${cfg.color}`}>
          {cfg.label}
        </span>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-gold-200/40 pt-5 sm:grid-cols-3">
        <Field label="Taille"     value={formatBytes(document.size_bytes)} />
        <Field label="Type"       value={document.mime_type.split("/")[1]?.toUpperCase() ?? document.mime_type} />
        <Field label="Avancement" value={`${document.progress_percent}%`} />
        <Field
          label="Téléversé"
          value={document.created_at ? new Date(document.created_at).toLocaleString("fr-TN", { dateStyle: "short", timeStyle: "short" }) : "—"}
        />
        <Field
          label="Terminé"
          value={document.finished_at ? new Date(document.finished_at).toLocaleString("fr-TN", { dateStyle: "short", timeStyle: "short" }) : "—"}
        />
        <Field label="Étape" value={document.progress_stage ?? "—"} />
      </div>
    </div>
  );
}
