import type { DocumentDetailResponse, ExtractionResponse } from "../types/documents";

export function ExtractionViewer({
  extraction,
  document,
}: {
  extraction: ExtractionResponse | null;
  document: DocumentDetailResponse | null;
}) {
  if (!document) {
    return (
      <div className="lex-panel p-6 text-sm leading-relaxed text-stone-500">
        Sélectionnez un document dans la bibliothèque pour inspecter les métadonnées et les résultats d'extraction.
      </div>
    );
  }

  if (!extraction?.extraction) {
    return (
      <div className="lex-panel p-6 text-sm leading-relaxed text-stone-500">
        {document.status === "failed"
          ? document.last_error || "L'extraction a échoué."
          : document.progress_message || "Le résultat d'extraction apparaîtra ici une fois le traitement terminé."}
      </div>
    );
  }

  const payload = extraction.extraction;

  return (
    <div className="lex-panel space-y-6 p-6 sm:p-7">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-700">Agent 1</p>
          <h2 className="font-display mt-1 text-xl font-medium text-stone-900">Résultat d'extraction</h2>
          <p className="mt-1 text-sm text-stone-500">{payload.document_metadata.filename}</p>
        </div>
      </div>

      {payload.warnings.length > 0 && (
        <div className="rounded-xl border border-amber-300/50 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-semibold">Avertissements</p>
          <ul className="mt-2 list-disc pl-5 space-y-1">
            {payload.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {payload.errors.length > 0 && (
        <div className="rounded-xl border border-rose-300/50 bg-rose-50 p-4 text-sm text-rose-900">
          <p className="font-semibold">Erreurs</p>
          <ul className="mt-2 list-disc pl-5 space-y-1">
            {payload.errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">Texte brut</h3>
          <pre className="max-h-96 overflow-auto rounded-xl border border-stone-200 bg-stone-100 p-4 text-sm text-stone-800 whitespace-pre-wrap font-mono">{payload.raw_text || "Aucun texte brut"}</pre>
        </section>
        <section>
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">Texte normalisé</h3>
          <pre className="max-h-96 overflow-auto rounded-xl border border-stone-200 bg-stone-100 p-4 text-sm text-stone-800 whitespace-pre-wrap font-mono">{payload.normalized_text || "Aucun texte normalisé"}</pre>
        </section>
      </div>

      <section>
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">Métadonnées de structure</h3>
        <pre className="overflow-auto rounded-xl border border-stone-200 bg-stone-100 p-4 text-xs text-stone-700 font-mono">{JSON.stringify(payload.structure ?? {}, null, 2)}</pre>
      </section>
    </div>
  );
}
