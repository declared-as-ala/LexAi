import { Link } from "react-router-dom";

const FEATURES = [
  {
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
    title: "Agent 1 — Extraction",
    desc: "Ingestion automatique de PDF, DOCX, TXT et HTML. Extraction du texte brut, normalisation et détection de la structure documentaire.",
    color: "from-blue-500 to-blue-400",
    badge: "blue",
  },
  {
    icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
    title: "Agent 2 — Analyse NLP",
    desc: "Segmentation des clauses, classification multi-label par XLM-RoBERTa fine-tuné, extraction d'entités juridiques (parties, durées, obligations).",
    color: "from-violet-500 to-violet-400",
    badge: "violet",
  },
  {
    icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
    title: "Agent 3 — Conformité",
    desc: "Évaluation par 44 règles juridiques LNPDP, RGPD, ISO 27001 et ISO 9001. Score de conformité pondéré et niveau de risque juridique global.",
    color: "from-emerald-500 to-emerald-400",
    badge: "emerald",
  },
  {
    icon: "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
    title: "Agent 4 — Recommandations",
    desc: "Génération de clauses révisées via templates juridiques validés et slot-filling depuis les entités NLP. Export en PDF et DOCX organisé.",
    color: "from-gold-500 to-gold-400",
    badge: "gold",
  },
];

const FRAMEWORKS = [
  { name: "LNPDP 2004-63", desc: "Loi tunisienne sur la protection des données personnelles" },
  { name: "RGPD EU 2016/679", desc: "Règlement général européen sur la protection des données" },
  { name: "ISO 27001:2022", desc: "Sécurité de l'information — systèmes de management" },
  { name: "ISO 9001:2015", desc: "Systèmes de management de la qualité" },
];

const STATS = [
  { value: "44", label: "Règles juridiques" },
  { value: "12", label: "Types de clauses" },
  { value: "4", label: "Agents IA" },
  { value: "50MB", label: "Taille max de fichier" },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-stone-900">

      {/* ── Hero ── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-stone-50 via-amber-50/40 to-white">
        <div className="pointer-events-none absolute inset-0 lex-grid-bg opacity-40" />
        <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 h-[500px] w-[800px] rounded-full bg-gold-400/10 blur-3xl" />

        <div className="relative mx-auto max-w-6xl px-4 py-24 sm:px-6 lg:px-8 lg:py-32">
          <div className="flex flex-col items-center text-center gap-8">

            {/* Badge */}
            <span className="inline-flex items-center gap-2 rounded-full border border-gold-300/60 bg-amber-50 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-gold-700">
              <span className="h-1.5 w-1.5 rounded-full bg-gold-500 animate-pulse" />
              Plateforme IA · Conformité Juridique
            </span>

            {/* Headline */}
            <h1 className="max-w-4xl text-4xl font-bold tracking-tight text-stone-900 sm:text-5xl lg:text-6xl leading-tight">
              Analysez vos contrats en{" "}
              <span className="bg-gradient-to-r from-gold-600 to-gold-400 bg-clip-text text-transparent">
                quelques secondes
              </span>
            </h1>

            <p className="max-w-2xl text-lg text-stone-500 leading-relaxed">
              LexAI automatise la revue de conformité de vos contrats juridiques face au{" "}
              <strong className="text-stone-700">droit tunisien (LNPDP)</strong>,{" "}
              <strong className="text-stone-700">RGPD</strong> et{" "}
              <strong className="text-stone-700">ISO 27001</strong> grâce à un pipeline
              de 4 agents IA spécialisés.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2.5 rounded-2xl bg-gradient-to-r from-gold-600 to-gold-500 px-8 py-3.5 text-base font-bold text-white shadow-[0_4px_20px_rgba(201,163,54,0.45)] transition-all hover:from-gold-700 hover:to-gold-600 hover:shadow-[0_6px_28px_rgba(201,163,54,0.55)] hover:-translate-y-0.5"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                Analyser un contrat
              </Link>
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-2 rounded-2xl border border-stone-300 bg-white px-8 py-3.5 text-base font-semibold text-stone-700 shadow-sm transition-all hover:border-gold-300 hover:text-gold-700 hover:-translate-y-0.5"
              >
                Comment ça marche
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>

            {/* Stats */}
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-6 w-full max-w-2xl">
              {STATS.map((s) => (
                <div key={s.label} className="text-center">
                  <p className="text-3xl font-bold text-gold-600">{s.value}</p>
                  <p className="mt-0.5 text-xs text-stone-500">{s.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-24 bg-white">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-xs font-bold uppercase tracking-widest text-gold-600">Pipeline IA</p>
            <h2 className="mt-2 text-3xl font-bold text-stone-900 sm:text-4xl">4 agents spécialisés</h2>
            <p className="mt-4 max-w-xl mx-auto text-stone-500">
              Chaque agent traite une étape précise du pipeline. Ensemble, ils transforment un document brut en rapport de conformité actionnable.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f, i) => (
              <div
                key={f.title}
                className="group relative overflow-hidden rounded-2xl border border-stone-100 bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-gold-200"
              >
                {/* Step number */}
                <div className="absolute top-4 right-4 text-4xl font-black text-stone-50 group-hover:text-gold-100 transition-colors">
                  0{i + 1}
                </div>

                <div className={`mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${f.color} shadow-md`}>
                  <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={f.icon} />
                  </svg>
                </div>

                <h3 className="mb-2 text-sm font-bold text-stone-800">{f.title}</h3>
                <p className="text-xs leading-relaxed text-stone-500">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Legal Frameworks ── */}
      <section className="py-20 bg-gradient-to-br from-stone-50 to-amber-50/30">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <p className="text-xs font-bold uppercase tracking-widest text-gold-600">Référentiels couverts</p>
            <h2 className="mt-2 text-3xl font-bold text-stone-900">Conformité multi-référentiels</h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FRAMEWORKS.map((fw) => (
              <div key={fw.name} className="rounded-2xl border border-gold-200/60 bg-white p-5 shadow-sm">
                <span className="inline-block rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-gold-700 border border-gold-200/60">
                  {fw.name}
                </span>
                <p className="mt-3 text-xs text-stone-500 leading-relaxed">{fw.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Supported formats ── */}
      <section className="py-20 bg-white">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-gold-600">Formats supportés</p>
          <h2 className="mt-2 text-3xl font-bold text-stone-900">Importez depuis n'importe quel format</h2>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            {["PDF", "DOCX", "DOC", "TXT", "HTML"].map((fmt) => (
              <span
                key={fmt}
                className="rounded-xl border border-stone-200 bg-stone-50 px-6 py-3 text-lg font-bold text-stone-700 shadow-sm"
              >
                .{fmt.toLowerCase()}
              </span>
            ))}
          </div>
          <p className="mt-6 text-sm text-stone-400">Taille maximale : 50 MB par fichier</p>
        </div>
      </section>

      {/* ── CTA Banner ── */}
      <section className="py-20 bg-gradient-to-r from-gold-600 via-gold-500 to-gold-400">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Prêt à analyser votre premier contrat ?
          </h2>
          <p className="mt-4 text-gold-100 text-lg">
            Téléversez votre document et obtenez un rapport de conformité complet en moins d'une minute.
          </p>
          <Link
            to="/analyze"
            className="mt-8 inline-flex items-center gap-2.5 rounded-2xl bg-white px-10 py-4 text-base font-bold text-gold-700 shadow-lg transition-all hover:bg-amber-50 hover:shadow-xl hover:-translate-y-0.5"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            Commencer maintenant
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-stone-100 bg-white py-10">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-gold-500 to-gold-400">
              <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.97z" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-stone-700">LexAI</span>
          </div>
          <p className="text-xs text-stone-400">
            Plateforme IA d'analyse de conformité juridique · Droit tunisien & RGPD
          </p>
        </div>
      </footer>

    </div>
  );
}
