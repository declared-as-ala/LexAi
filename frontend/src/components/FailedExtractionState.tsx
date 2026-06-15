export function FailedExtractionState({
  error,
  onRetry,
  retrying = false,
}: {
  error: string | null | undefined;
  onRetry: () => void;
  retrying?: boolean;
}) {
  return (
    <div className="lex-panel border-rose-200/60 bg-gradient-to-br from-rose-50 to-red-50 p-6 sm:p-7 ring-1 ring-rose-200/50">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-rose-200/70 bg-rose-100 text-rose-600">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-rose-600">Échec</p>
          <h2 className="font-display mt-1 text-xl font-medium text-stone-900">Extraction interrompue</h2>
          <p className="mt-2 text-sm leading-relaxed text-rose-800/90">{error || "Erreur d'extraction inconnue."}</p>
        </div>
      </div>
      <button
        type="button"
        onClick={onRetry}
        disabled={retrying}
        className="mt-5 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-rose-600 to-rose-500 px-5 py-2.5 text-sm font-bold text-white shadow-[0_6px_20px_-8px_rgba(244,63,94,0.50)] transition hover:brightness-110 disabled:opacity-60"
      >
        {retrying ? (
          <>
            <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Relance en cours…
          </>
        ) : (
          <>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
            Relancer l'extraction
          </>
        )}
      </button>
    </div>
  );
}
