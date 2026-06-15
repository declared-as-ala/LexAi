export function EmptyWorkspaceState() {
  const agents = [
    { label: "Extract",   color: "text-teal-700",    border: "border-teal-300/50",    bg: "bg-teal-50",    num: "1" },
    { label: "Analyze",   color: "text-violet-700",  border: "border-violet-300/50",  bg: "bg-violet-50",  num: "2" },
    { label: "Evaluate",  color: "text-indigo-700",  border: "border-indigo-300/50",  bg: "bg-indigo-50",  num: "3" },
    { label: "Recommend", color: "text-fuchsia-700", border: "border-fuchsia-300/50", bg: "bg-fuchsia-50", num: "4" },
  ];

  return (
    <div className="lex-panel animate-fade-in flex flex-col items-center justify-center px-6 py-16 text-center sm:px-10">
      {/* Central icon */}
      <div className="relative">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl border border-gold-300/50 bg-gradient-to-br from-amber-50 to-yellow-50 shadow-[0_0_50px_-16px_rgba(201,163,54,0.45)]">
          <svg
            className="h-10 w-10 text-gold-600 animate-float"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.1}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        </div>
        {/* Orbiting glow */}
        <div className="pointer-events-none absolute -inset-3 rounded-3xl border border-gold-300/25 animate-pulse" />
      </div>

      <h2 className="font-display mt-6 text-2xl font-semibold text-stone-900">
        Bureau vide
      </h2>
      <p className="mt-3 max-w-sm text-sm leading-relaxed text-stone-500">
        Téléversez un contrat depuis le panneau gauche — PDF, DOCX, TXT, HTML ou image
        (JPG, PNG via OCR). LexAI lancera automatiquement le pipeline complet.
      </p>

      {/* Pipeline mini-steps */}
      <div className="mt-8 flex items-center gap-0">
        {agents.map((ag, i) => (
          <div key={ag.label} className="flex items-center">
            {i > 0 && (
              <div className="mx-2 h-px w-8 bg-gradient-to-r from-stone-300/60 to-stone-200/30" />
            )}
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-xl border text-xs font-bold shadow-sm ${ag.border} ${ag.bg} ${ag.color}`}
                style={{ animationDelay: `${i * 150}ms` }}
              >
                {ag.num}
              </div>
              <span className={`text-[9px] font-bold uppercase tracking-wide ${ag.color} opacity-80`}>
                {ag.label}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Legal frameworks */}
      <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
        {["LNPDP 2004-63", "RGPD EU 2016", "ISO 27001", "ISO 9001", "COC Tunisie"].map((fw) => (
          <span
            key={fw}
            className="rounded-full border border-gold-200/60 bg-amber-50/80 px-3 py-1 text-[10px] font-semibold text-gold-700"
          >
            {fw}
          </span>
        ))}
      </div>
    </div>
  );
}
