import { useRef, useState } from "react";

interface UploadDropzoneProps {
  onFilesSelect: (files: File[]) => void;
  loading?: boolean;
  agent4LlmEnabled?: boolean | null;
  imageOcrSupported?: boolean | null;
}

export function UploadDropzone({
  onFilesSelect,
  loading = false,
  agent4LlmEnabled = null,
  imageOcrSupported = true,
}: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragging, setDragging] = useState(false);

  const submitFiles = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    onFilesSelect(Array.from(fileList));
  };

  return (
    <div className="lex-panel animate-slide-up p-4 sm:p-5">
      {/* Header row */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">
            Ingestion
          </p>
          <p className="text-sm font-semibold text-stone-900">Téléverser un document</p>
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          {imageOcrSupported !== false && (
            <span className="rounded-full border border-teal-400/40 bg-teal-50 px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-teal-700">
              OCR · IMG
            </span>
          )}
          {agent4LlmEnabled === true && (
            <span className="rounded-full border border-fuchsia-400/40 bg-fuchsia-50 px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-fuchsia-700">
              LLM actif
            </span>
          )}
          {agent4LlmEnabled === false && (
            <span className="rounded-full border border-stone-300 bg-stone-100 px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-stone-500">
              Templates
            </span>
          )}
        </div>
      </div>

      {/* Drop zone */}
      <div
        onClick={() => !loading && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); if (!loading) setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); submitFiles(e.dataTransfer.files); }}
        className={`relative flex min-h-[10.5rem] cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed p-6 text-center transition-all duration-300 ${
          dragging
            ? "scale-[1.01] border-gold-400 bg-gradient-to-b from-amber-50 to-yellow-50 shadow-[0_0_40px_-8px_rgba(201,163,54,0.35)]"
            : loading
            ? "cursor-not-allowed border-stone-200 bg-stone-50/60"
            : "border-stone-300/60 bg-stone-50/40 hover:border-gold-300/70 hover:bg-amber-50/40 hover:shadow-[0_0_28px_-12px_rgba(201,163,54,0.20)]"
        }`}
      >
        {/* Dragging corner accents */}
        {dragging && (
          <>
            <div className="pointer-events-none absolute left-0 top-0 h-6 w-6 rounded-tl-xl border-l-2 border-t-2 border-gold-500" />
            <div className="pointer-events-none absolute right-0 top-0 h-6 w-6 rounded-tr-xl border-r-2 border-t-2 border-gold-500" />
            <div className="pointer-events-none absolute bottom-0 left-0 h-6 w-6 rounded-bl-xl border-b-2 border-l-2 border-gold-500" />
            <div className="pointer-events-none absolute bottom-0 right-0 h-6 w-6 rounded-br-xl border-b-2 border-r-2 border-gold-500" />
          </>
        )}

        {loading ? (
          <div className="flex flex-col items-center">
            <div className="relative flex h-14 w-14 items-center justify-center">
              <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-gold-500 border-r-gold-400/50" />
              <svg className="h-6 w-6 text-gold-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <p className="mt-3 text-sm font-semibold text-gold-800">Téléversement en cours…</p>
            <div className="mt-1 flex gap-1">
              <span className="dot-1 h-1.5 w-1.5 rounded-full bg-gold-500" />
              <span className="dot-2 h-1.5 w-1.5 rounded-full bg-gold-500" />
              <span className="dot-3 h-1.5 w-1.5 rounded-full bg-gold-500" />
            </div>
          </div>
        ) : (
          <>
            <div
              className={`flex h-14 w-14 items-center justify-center rounded-2xl border transition-all duration-300 ${
                dragging
                  ? "border-gold-400/70 bg-gold-50 shadow-[0_0_24px_rgba(201,163,54,0.30)]"
                  : "border-stone-200 bg-white shadow-sm"
              }`}
            >
              <svg
                className={`transition-all duration-300 ${dragging ? "animate-bounce-up h-7 w-7 text-gold-600" : "h-7 w-7 text-stone-400"}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>

            <p className={`mt-3 text-base font-semibold transition-colors duration-200 ${dragging ? "text-gold-800" : "text-stone-800"}`}>
              {dragging ? "Relâchez pour téléverser" : "Glissez un contrat ici"}
            </p>
            <p className="mt-1 text-xs leading-relaxed text-stone-500">
              PDF, DOCX, TXT, HTML · Images JPG/PNG via OCR
            </p>
            <button
              type="button"
              className="mt-4 rounded-xl bg-gradient-to-r from-gold-500 to-gold-400 px-5 py-2 text-sm font-bold text-white shadow-[0_4px_18px_-4px_rgba(201,163,54,0.50)] transition-all duration-200 hover:brightness-110 hover:shadow-[0_8px_26px_-4px_rgba(201,163,54,0.60)] active:scale-[0.97]"
              onClick={(e) => e.stopPropagation()}
            >
              Parcourir les fichiers
            </button>
          </>
        )}

        <input
          ref={inputRef}
          type="file"
          className="hidden"
          multiple
          accept=".pdf,.doc,.docx,.txt,.html,.htm,.jpg,.jpeg,.png,.tif,.tiff,.bmp,.webp"
          onChange={(e) => submitFiles(e.target.files)}
        />
      </div>

      {/* Format chips */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {["PDF", "DOCX", "TXT", "HTML", "PNG", "JPG"].map((fmt) => (
          <span
            key={fmt}
            className="rounded-md border border-stone-200 bg-white px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-stone-500 shadow-sm"
          >
            {fmt}
          </span>
        ))}
      </div>
    </div>
  );
}
