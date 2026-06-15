import type { DocumentStatus } from "../types/documents";

const STEPS = [
  {
    label: "Extract",
    sub: "Agent 1",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
    ),
    doneColor:      "border-teal-400/50 bg-teal-50 text-teal-700",
    activeColor:    "border-gold-400/70 bg-amber-50 text-gold-800",
    connectorDone:  "from-teal-400/60 to-teal-400/30",
  },
  {
    label: "Analyze",
    sub: "Agent 2",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
      </svg>
    ),
    doneColor:      "border-violet-400/50 bg-violet-50 text-violet-700",
    activeColor:    "border-gold-400/70 bg-amber-50 text-gold-800",
    connectorDone:  "from-violet-400/60 to-violet-400/30",
  },
  {
    label: "Evaluate",
    sub: "Agent 3",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.97z" />
      </svg>
    ),
    doneColor:      "border-indigo-400/50 bg-indigo-50 text-indigo-700",
    activeColor:    "border-gold-400/70 bg-amber-50 text-gold-800",
    connectorDone:  "from-indigo-400/60 to-indigo-400/30",
  },
  {
    label: "Recommend",
    sub: "Agent 4",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
    doneColor:      "border-fuchsia-400/50 bg-fuchsia-50 text-fuchsia-700",
    activeColor:    "border-gold-400/70 bg-amber-50 text-gold-800",
    connectorDone:  "from-fuchsia-400/60 to-fuchsia-400/30",
  },
] as const;

function activeStage(status: DocumentStatus | undefined): number {
  if (!status || status === "uploaded") return 0;
  if (status === "failed") return -1;
  if (["queued", "extracting", "extracted"].includes(status)) return 0;
  if (["analyzing", "analyzed"].includes(status)) return 1;
  if (["evaluating", "evaluated"].includes(status)) return 2;
  if (status === "recommending") return 3;
  if (status === "complete") return 4;
  return 0;
}

export function AgentPipeline({ status }: { status: DocumentStatus | undefined }) {
  const stage = activeStage(status);
  const failed = status === "failed";
  const complete = status === "complete";

  return (
    <div className="w-full">
      <div className="flex w-full items-center">
        {STEPS.map((step, i) => {
          const done = !failed && (stage > i || complete);
          const current = !failed && !complete && stage === i;
          const segDone = !failed && stage > i;

          return (
            <div key={step.label} className="flex min-w-0 flex-1 items-center last:flex-none">
              {/* Connector line */}
              {i > 0 && (
                <div className="relative mx-1.5 h-[2px] min-w-[16px] flex-1 overflow-hidden rounded-full bg-stone-200">
                  <div
                    className={`progress-bar-smooth absolute inset-y-0 left-0 rounded-full bg-gradient-to-r ${
                      failed ? "w-0" : segDone ? `w-full ${step.connectorDone}` : "w-0"
                    }`}
                  />
                </div>
              )}

              {/* Step node */}
              <div className="flex shrink-0 flex-col items-center">
                <div
                  className={`relative flex h-11 w-11 items-center justify-center rounded-xl border transition-all duration-500 shadow-sm ${
                    failed
                      ? i === 0
                        ? "border-rose-300/60 bg-rose-50 text-rose-600"
                        : "border-stone-200 bg-stone-100/60 text-stone-400"
                      : done
                      ? step.doneColor
                      : current
                      ? `${step.activeColor} animate-pulse-ring shadow-md`
                      : "border-stone-200 bg-stone-100/60 text-stone-400"
                  }`}
                >
                  {done ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : failed && i === 0 ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  ) : current ? (
                    <div className="animate-spin-slow">{step.icon}</div>
                  ) : (
                    step.icon
                  )}
                </div>

                {/* Labels */}
                <span
                  className={`mt-2 text-center text-[10px] font-bold uppercase leading-tight tracking-wide transition-colors duration-300 ${
                    current && !failed
                      ? "text-gold-700"
                      : done
                      ? "text-stone-700"
                      : "text-stone-400"
                  }`}
                >
                  {step.label}
                </span>
                <span
                  className={`mt-0.5 hidden text-[9px] font-medium sm:block transition-colors duration-300 ${
                    current ? "text-gold-600" : done ? "text-stone-500" : "text-stone-400"
                  }`}
                >
                  {step.sub}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Status message */}
      <div className="mt-3 text-center text-[11px] font-medium">
        {complete && (
          <p className="animate-fade-in text-emerald-700">
            ✓ Tous les agents ont terminé avec succès
          </p>
        )}
        {failed && (
          <p className="text-rose-600">
            Erreur de traitement — vérifiez le document ou relancez
          </p>
        )}
        {!status && (
          <p className="text-stone-400">En attente d'un document…</p>
        )}
      </div>
    </div>
  );
}
