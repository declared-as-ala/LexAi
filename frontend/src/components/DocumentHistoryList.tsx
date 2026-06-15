import type { DocumentBaseResponse } from "../types/documents";
import { DocumentHistoryItem } from "./DocumentHistoryItem";

export function DocumentHistoryList({
  documents,
  selectedDocumentId,
  onSelect,
  onDelete,
  deletingId,
  loading,
}: {
  documents: DocumentBaseResponse[];
  selectedDocumentId: number | null;
  onSelect: (id: number) => void;
  onDelete: (id: number) => void;
  deletingId?: number | null;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="lex-panel space-y-2 p-4 sm:p-5">
        <p className="font-display text-sm font-medium text-stone-900">Documents</p>
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-stone-200/70" />
        ))}
      </div>
    );
  }

  return (
    <div className="lex-panel overflow-hidden">
      <div className="flex items-center justify-between border-b border-gold-200/40 px-4 py-3.5 sm:px-5">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">Library</p>
          <p className="font-display text-sm font-medium text-stone-900">Documents</p>
        </div>
        <span className="rounded-full border border-gold-300/40 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-gold-700">
          {documents.length}
        </span>
      </div>
      <div className="p-3 sm:p-4">
        {documents.length === 0 ? (
          <p className="py-6 text-center text-sm text-stone-500">Aucun document téléversé.</p>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <DocumentHistoryItem
                key={doc.id}
                document={doc}
                selected={doc.id === selectedDocumentId}
                onSelect={onSelect}
                onDelete={onDelete}
                deleting={deletingId === doc.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
