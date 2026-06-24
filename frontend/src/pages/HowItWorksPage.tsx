import { Link } from "react-router-dom";

const STEPS = [
  {
    num: "01",
    color: "from-blue-500 to-blue-400",
    ring: "ring-blue-200",
    bg: "bg-blue-50",
    text: "text-blue-700",
    title: "Agent 1 — Extraction documentaire",
    subtitle: "PDF · DOCX · TXT · HTML",
    desc: "L'agent 1 accepte votre fichier, valide son format et sa taille (max 50 Mo), puis en extrait le texte brut via PyMuPDF (PDF), python-docx (DOCX) ou BeautifulSoup4 (HTML). Le texte est ensuite normalisé : encodage UTF-8, fins de ligne uniformes, espaces multiples supprimés.",
    details: [
      "Validation MIME + extension",
      "Extraction asynchrone via Celery",
      "Normalisation et détection de structure",
      "Suivi de progression en temps réel",
    ],
    output: "Texte normalisé + métadonnées de structure",
  },
  {
    num: "02",
    color: "from-violet-500 to-violet-400",
    ring: "ring-violet-200",
    bg: "bg-violet-50",
    text: "text-violet-700",
    title: "Agent 2 — Analyse NLP",
    subtitle: "XLM-RoBERTa · spaCy · Entités",
    desc: "L'agent 2 segmente le texte en clauses, les classifie selon 12 types (obligation, confidentialité, responsabilité…) grâce à XLM-RoBERTa fine-tuné sur CUAD + LEDGAR + données synthétiques françaises, puis extrait les entités juridiques clés (parties, durées, montants).",
    details: [
      "Segmentation par frontières de clauses",
      "Classification multi-label (12 types)",
      "NER : parties, dates, montants, rôles",
      "Score de confiance par clause",
    ],
    output: "Clauses segmentées + labels + entités",
  },
  {
    num: "03",
    color: "from-emerald-500 to-emerald-400",
    ring: "ring-emerald-200",
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    title: "Agent 3 — Évaluation de conformité",
    subtitle: "LNPDP · RGPD · ISO 27001 · ISO 9001",
    desc: "L'agent 3 applique 44 règles juridiques encodées en JSON contre les clauses annotées. Pour chaque violation, il calcule un score par référentiel selon la formule : score = max(0, 100 − Σ poids_sévérité). Le score global est une moyenne pondérée multi-référentiels.",
    details: [
      "15 règles LNPDP + 12 RGPD + 12 ISO 27001 + 5 ISO 9001",
      "Sévérités : critique (−30), élevée (−20), moyenne (−10), faible (−5)",
      "Détection des clauses obligatoires manquantes",
      "Niveau de risque juridique : faible / moyen / élevé / critique",
    ],
    output: "Score 0–100 + violations + risque juridique",
  },
  {
    num: "04",
    color: "from-gold-500 to-gold-400",
    ring: "ring-gold-200",
    bg: "bg-amber-50",
    text: "text-gold-700",
    title: "Agent 4 — Recommandations",
    subtitle: "Templates · Slot-filling · Export",
    desc: "L'agent 4 produit pour chaque violation une clause de remplacement rédigée en français juridique via 24 templates validés et un mécanisme de slot-filling depuis les entités NLP. Le juriste accepte ou refuse chaque proposition, puis exporte le contrat révisé en PDF ou DOCX structuré.",
    details: [
      "24 templates LNPDP / RGPD / ISO",
      "Slot-filling : {DURATION}, {PARTY}, {ROLE}…",
      "Fallback générique si aucun template",
      "Export PDF structuré + DOCX avec clauses surlignées",
    ],
    output: "Contrat révisé exportable (PDF / DOCX)",
  },
];

export function HowItWorksPage() {
  return (
    <div className="min-h-screen bg-white">

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-stone-50 via-amber-50/30 to-white py-20">
        <div className="pointer-events-none absolute inset-0 lex-grid-bg opacity-30" />
        <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
          <span className="inline-block rounded-full border border-gold-300/60 bg-amber-50 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-gold-700">
            Architecture technique
          </span>
          <h1 className="mt-4 text-4xl font-bold tracking-tight text-stone-900 sm:text-5xl">
            Comment fonctionne LexAI ?
          </h1>
          <p className="mt-5 max-w-2xl mx-auto text-lg text-stone-500 leading-relaxed">
            Un pipeline de 4 agents IA orchestrés par LangGraph transforme votre
            document juridique brut en rapport de conformité actionnable.
          </p>
        </div>
      </section>

      {/* Pipeline overview */}
      <section className="py-16 bg-white">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">

          {/* Flow arrows */}
          <div className="flex items-center justify-center gap-2 mb-14 flex-wrap">
            {["Upload", "Extraction", "NLP", "Conformité", "Recommandations", "Export"].map((step, i, arr) => (
              <div key={step} className="flex items-center gap-2">
                <span className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-xs font-semibold text-stone-600">
                  {step}
                </span>
                {i < arr.length - 1 && (
                  <svg className="h-4 w-4 text-gold-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </div>
            ))}
          </div>

          {/* Agent cards */}
          <div className="space-y-10">
            {STEPS.map((step, i) => (
              <div key={step.num} className="group relative flex flex-col lg:flex-row gap-6 rounded-2xl border border-stone-100 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">

                {/* Number badge */}
                <div className="shrink-0">
                  <div className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${step.color} shadow-md`}>
                    <span className="text-xl font-black text-white">{step.num}</span>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <h3 className="text-lg font-bold text-stone-900">{step.title}</h3>
                    <span className={`rounded-full ${step.bg} ${step.text} px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide`}>
                      {step.subtitle}
                    </span>
                  </div>

                  <p className="text-sm text-stone-500 leading-relaxed mb-4">{step.desc}</p>

                  <div className="grid sm:grid-cols-2 gap-1.5 mb-4">
                    {step.details.map((d) => (
                      <div key={d} className="flex items-start gap-2">
                        <svg className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${step.text}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-xs text-stone-600">{d}</span>
                      </div>
                    ))}
                  </div>

                  {/* Output tag */}
                  <div className={`inline-flex items-center gap-1.5 rounded-lg border ${step.ring} ${step.bg} px-3 py-1.5`}>
                    <svg className={`h-3.5 w-3.5 ${step.text}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                    <span className={`text-xs font-semibold ${step.text}`}>Sortie : {step.output}</span>
                  </div>
                </div>

                {/* Connector to next */}
                {i < STEPS.length - 1 && (
                  <div className="absolute -bottom-6 left-10 flex h-12 w-7 items-center justify-center lg:left-10">
                    <div className="h-full w-px bg-gradient-to-b from-stone-200 to-transparent" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech stack */}
      <section className="py-20 bg-gradient-to-br from-stone-50 to-amber-50/20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <p className="text-xs font-bold uppercase tracking-widest text-gold-600">Stack technique</p>
            <h2 className="mt-2 text-3xl font-bold text-stone-900">Technologies utilisées</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { layer: "API", tech: "FastAPI + Celery + Redis" },
              { layer: "Base de données", tech: "PostgreSQL 16 + SQLAlchemy 2" },
              { layer: "NLP", tech: "spaCy 3.7 + HuggingFace Transformers" },
              { layer: "Modèle", tech: "XLM-RoBERTa base (fine-tuné)" },
              { layer: "Orchestration", tech: "LangGraph 0.2" },
              { layer: "Frontend", tech: "React 18 + TypeScript + Tailwind" },
              { layer: "Extraction", tech: "PyMuPDF + python-docx + BeautifulSoup4" },
              { layer: "Déploiement", tech: "Docker Compose + GitHub Actions + VPS" },
              { layer: "LLM optionnel", tech: "Groq API (Llama 3 / Mixtral)" },
            ].map((t) => (
              <div key={t.layer} className="rounded-xl border border-stone-100 bg-white p-4 shadow-sm">
                <p className="text-[10px] font-bold uppercase tracking-widest text-gold-600">{t.layer}</p>
                <p className="mt-1 text-sm font-semibold text-stone-800">{t.tech}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-white">
        <div className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-stone-900">Prêt à l'essayer ?</h2>
          <p className="mt-4 text-stone-500">Téléversez votre premier contrat et voyez le pipeline en action.</p>
          <Link
            to="/analyze"
            className="mt-8 inline-flex items-center gap-2.5 rounded-2xl bg-gradient-to-r from-gold-600 to-gold-500 px-10 py-4 text-base font-bold text-white shadow-[0_4px_20px_rgba(201,163,54,0.40)] hover:shadow-[0_6px_28px_rgba(201,163,54,0.55)] hover:-translate-y-0.5 transition-all"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            Analyser un contrat
          </Link>
        </div>
      </section>

    </div>
  );
}
