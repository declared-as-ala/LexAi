#!/usr/bin/env python3
"""Generate all UML diagrams for the LexAI PFE rapport."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Ellipse, FancyBboxPatch
import os

OUT = r"c:/Users/Ala/Desktop/PFE/rapport/images"
os.makedirs(OUT, exist_ok=True)
plt.rcParams['font.family'] = 'DejaVu Sans'

BLUE='#2471A3'; DBLUE='#1A5276'; LBLUE='#D6EAF8'
GRAY='#808B96'; BLACK='#1C2833'; WHITE='#FFFFFF'

# ── primitives ─────────────────────────────────────────────────────────────────

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print(f"  OK  {name}")

def uc_fig(w=12, h=8):
    fig, ax = plt.subplots(figsize=(w,h), dpi=150)
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0,w); ax.set_ylim(0,h); ax.set_aspect('equal'); ax.axis('off')
    return fig, ax

def actor(ax, cx, cy, label, color=BLACK, fs=8.5):
    ax.add_patch(plt.Circle((cx, cy+0.30), 0.15, color=color, fill=False, lw=2, zorder=6))
    ax.plot([cx,cx],          [cy+0.15, cy-0.07], color=color, lw=2, zorder=6)
    ax.plot([cx-0.22,cx+0.22],[cy+0.06, cy+0.06], color=color, lw=2, zorder=6)
    ax.plot([cx,cx-0.18],     [cy-0.07, cy-0.38], color=color, lw=2, zorder=6)
    ax.plot([cx,cx+0.18],     [cy-0.07, cy-0.38], color=color, lw=2, zorder=6)
    for i, ln in enumerate(label.split('\n')):
        ax.text(cx, cy-0.55-i*0.17, ln, ha='center', va='top', fontsize=fs, color=color, fontweight='bold')

def uc_el(ax, cx, cy, rw, rh, text, fc=LBLUE, ec=BLUE, fs=8):
    ax.add_patch(Ellipse((cx,cy), rw*2, rh*2, facecolor=fc, edgecolor=ec, lw=1.8, zorder=4))
    lines = text.split('\n'); dy=0.16; y0=cy+(len(lines)-1)*dy/2
    for i, ln in enumerate(lines):
        ax.text(cx, y0-i*dy, ln, ha='center', va='center', fontsize=fs, color=BLACK, zorder=5)

def boundary(ax, x, y, w, h, title):
    ax.add_patch(FancyBboxPatch((x,y), w, h, boxstyle='square,pad=0',
                 facecolor='#FAFBFC', edgecolor=GRAY, lw=1.5, linestyle='--', zorder=2))
    ax.text(x+0.12, y+h-0.14, title, ha='left', va='top', fontsize=8, fontstyle='italic', color=GRAY)

def assoc(ax, x1, y1, x2, y2):
    ax.plot([x1,x2],[y1,y2], color='#566573', lw=1.1, zorder=3)

def uc_header(ax, text, w=12):
    ax.text(w/2, 0.22, text, ha='center', va='center', fontsize=10, fontweight='bold', color=WHITE,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=BLUE, edgecolor='none'))

# ── sequence helpers ────────────────────────────────────────────────────────────

def seq_fig(parts, w=15, h=10):
    fig, ax = plt.subplots(figsize=(w,h), dpi=150)
    fig.patch.set_facecolor(WHITE); ax.set_xlim(0,w); ax.set_ylim(0,h); ax.axis('off')
    n = len(parts)
    xs = [w*(i+0.5)/n for i in range(n)]
    for x, name in zip(xs, parts):
        lines = name.split('\n'); bh = 0.30*len(lines)+0.22; by = h-0.4-bh
        ax.add_patch(FancyBboxPatch((x-0.85,by), 1.7, bh, boxstyle='round,pad=0.06',
                     facecolor=BLUE, edgecolor=DBLUE, lw=1.5, zorder=4))
        mid = by+bh/2
        for j, ln in enumerate(lines):
            ax.text(x, mid+(len(lines)-1-j)*0.15-(len(lines)-1)*0.075, ln,
                    ha='center', va='center', fontsize=7.5, color=WHITE, fontweight='bold', zorder=5)
        ax.plot([x,x],[by,0.35], color='#BDC3C7', lw=1, ls='--', zorder=1)
    return fig, ax, xs

def arrow(ax, xs, i, j, y, label, ret=False, fs=7.5):
    x1,x2 = xs[i],xs[j]
    c = GRAY if ret else BLACK
    # For return arrows draw right-to-left with dashed line
    ax.annotate('', xy=(x2,y), xytext=(x1,y),
                arrowprops=dict(arrowstyle='->', color=c, lw=1.3, mutation_scale=13,
                                linestyle='dashed' if ret else 'solid'))
    ax.text((x1+x2)/2, y+0.12, label, ha='center', va='bottom', fontsize=fs,
            color=c, style='italic' if ret else 'normal')

def note(ax, y, text):
    ax.text(0.10, y, text, ha='left', va='bottom', fontsize=6.8, color=GRAY, style='italic')

def seq_header(ax, text, w):
    ax.text(w/2, 0.15, text, ha='center', va='center', fontsize=10, fontweight='bold', color=WHITE,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=BLUE, edgecolor='none'))

def divider(ax, y, w, label):
    ax.plot([0.1, w-0.1], [y,y], color='#E5E7E9', lw=0.8, ls=':')
    ax.text(0.12, y+0.05, label, fontsize=6.8, color=GRAY, style='italic')

# ════════════════════════════════════════════════════════════════════════════════
# USE CASE DIAGRAMS
# ════════════════════════════════════════════════════════════════════════════════

def uc_sprint1():
    fig, ax = uc_fig()
    boundary(ax, 2.0, 0.75, 9.3, 6.55, 'Plateforme LexAI — Agent 1 : Extraction documentaire')
    actor(ax, 0.75, 4.8, 'Juriste')
    actor(ax, 0.75, 2.0, 'Administrateur')
    ucs = [
        (6.65, 6.1, 1.72, 0.38, 'Téléverser un contrat\n(PDF/DOCX/TXT/HTML)'),
        (6.65, 4.85,1.60, 0.34, 'Suivre la progression\ndu traitement'),
        (6.65, 3.65,1.60, 0.34, 'Consulter les résultats\nd\'extraction'),
        (6.65, 2.5, 1.55, 0.32, 'Relancer un traitement\néchoutant'),
        (6.65, 1.38,1.45, 0.30, 'Supprimer un document'),
    ]
    for args in ucs: uc_el(ax, *args)
    assoc(ax, 1.12, 4.8, 4.93, 6.1)
    assoc(ax, 1.12, 4.8, 5.05, 4.85)
    assoc(ax, 1.12, 4.8, 5.05, 3.65)
    assoc(ax, 1.12, 4.8, 5.10, 1.38)
    assoc(ax, 1.12, 2.0, 5.10, 2.5)
    assoc(ax, 1.12, 2.0, 5.10, 1.38)
    uc_header(ax, "Diagramme de cas d'utilisation — Sprint 1 : Agent 1 — Extraction documentaire")
    save(fig, 'uc_sprint1.png')

def uc_sprint2():
    fig, ax = uc_fig()
    boundary(ax, 2.0, 0.75, 9.3, 6.55, 'Plateforme LexAI — Agent 2 : Analyse NLP')
    actor(ax, 0.75, 5.0, 'Juriste')
    actor(ax, 0.75, 1.9, 'Système\n(Auto)')
    ucs = [
        (6.65, 6.1, 1.60, 0.34, 'Déclencher l\'analyse\nNLP manuellement'),
        (6.65, 4.9, 1.60, 0.34, 'Consulter les clauses\nsegmentées'),
        (6.65, 3.75,1.60, 0.34, 'Filtrer par label\net flag de conformité'),
        (6.65, 2.6, 1.65, 0.34, 'Consulter les entités\njuridiques extraites'),
        (6.65, 1.45,1.55, 0.30, 'Consulter le score\nde confiance'),
    ]
    for args in ucs: uc_el(ax, *args)
    assoc(ax, 1.12, 5.0, 5.05, 6.1)
    assoc(ax, 1.12, 5.0, 5.05, 4.9)
    assoc(ax, 1.12, 5.0, 5.05, 3.75)
    assoc(ax, 1.12, 5.0, 5.05, 2.6)
    assoc(ax, 1.12, 5.0, 5.10, 1.45)
    assoc(ax, 1.12, 1.9, 5.05, 6.1)
    uc_header(ax, "Diagramme de cas d'utilisation — Sprint 2 : Agent 2 — Analyse NLP")
    save(fig, 'uc_sprint2.png')

def uc_sprint3():
    fig, ax = uc_fig()
    boundary(ax, 2.0, 0.75, 9.3, 6.55, 'Plateforme LexAI — Agent 3 : Évaluation de conformité')
    actor(ax, 0.75, 5.0, 'Responsable\nconformité')
    actor(ax, 0.75, 1.9, 'Juriste')
    ucs = [
        (6.65, 6.1, 1.72, 0.34, 'Consulter le score\nde conformité global'),
        (6.65, 4.9, 1.70, 0.34, 'Consulter les violations\npar référentiel'),
        (6.65, 3.75,1.72, 0.34, 'Consulter les clauses\nobligatoires manquantes'),
        (6.65, 2.6, 1.60, 0.34, 'Identifier le niveau\nde risque juridique'),
        (6.65, 1.45,1.55, 0.30, 'Re-déclencher\nl\'évaluation'),
    ]
    for args in ucs: uc_el(ax, *args)
    assoc(ax, 1.12, 5.0, 4.93, 6.1)
    assoc(ax, 1.12, 5.0, 4.95, 4.9)
    assoc(ax, 1.12, 5.0, 4.93, 3.75)
    assoc(ax, 1.12, 5.0, 5.05, 2.6)
    assoc(ax, 1.12, 1.9, 5.10, 1.45)
    assoc(ax, 1.12, 1.9, 4.93, 6.1)
    uc_header(ax, "Diagramme de cas d'utilisation — Sprint 3 : Agent 3 — Évaluation de conformité")
    save(fig, 'uc_sprint3.png')

def uc_sprint4():
    fig, ax = uc_fig()
    boundary(ax, 2.0, 0.75, 9.3, 6.55, 'Plateforme LexAI — Agent 4 : Génération de recommandations')
    actor(ax, 0.75, 4.4, 'Juriste')
    ucs = [
        (6.65, 6.1, 1.72, 0.34, 'Consulter les\nrecommandations'),
        (6.65, 4.9, 1.70, 0.34, 'Accepter une\nrecommandation'),
        (6.65, 3.75,1.70, 0.34, 'Rejeter une\nrecommandation'),
        (6.65, 2.6, 1.80, 0.34, 'Exporter le contrat\nrévisé (DOCX / PDF)'),
        (6.65, 1.45,1.70, 0.30, 'Re-générer les\nrecommandations'),
    ]
    for args in ucs: uc_el(ax, *args)
    assoc(ax, 1.12, 4.4, 4.93, 6.1)
    assoc(ax, 1.12, 4.4, 4.95, 4.9)
    assoc(ax, 1.12, 4.4, 4.95, 3.75)
    assoc(ax, 1.12, 4.4, 4.85, 2.6)
    assoc(ax, 1.12, 4.4, 4.95, 1.45)
    uc_header(ax, "Diagramme de cas d'utilisation — Sprint 4 : Agent 4 — Génération de recommandations")
    save(fig, 'uc_sprint4.png')

# ════════════════════════════════════════════════════════════════════════════════
# SEQUENCE DIAGRAMS
# ════════════════════════════════════════════════════════════════════════════════

def seq_sprint1():
    parts = ['Juriste', 'API\nFastAPI', 'Worker\nCelery', 'Provider\n(PDF/DOCX…)', 'PostgreSQL']
    fig, ax, xs = seq_fig(parts, w=15, h=10)
    y, s = 8.30, 0.58
    divider(ax, y+0.12, 15, '1 — Téléversement')
    arrow(ax, xs, 0, 1, y, 'POST /documents/upload  (fichier)'); y -= s
    arrow(ax, xs, 1, 4, y, 'INSERT documents  (status = queued)'); y -= s
    arrow(ax, xs, 4, 1, y, 'document_id', ret=True); y -= s*0.6
    arrow(ax, xs, 1, 0, y, '201  { document_id }', ret=True); y -= s
    divider(ax, y+0.10, 15, '2 — Traitement asynchrone Celery')
    arrow(ax, xs, 1, 2, y, 'enqueue_extraction(document_id)'); y -= s
    arrow(ax, xs, 2, 4, y, 'UPDATE  status = extracting  (10 %)'); y -= s
    divider(ax, y+0.10, 15, '3 — Extraction selon le type MIME')
    arrow(ax, xs, 2, 3, y, 'get_provider(mime_type)  →  PdfProvider / DocxProvider…'); y -= s
    arrow(ax, xs, 2, 3, y, 'provider.extract(file_path)'); y -= s
    arrow(ax, xs, 3, 2, y, 'ExtractionArtifact  (raw_text, structure_json)', ret=True); y -= s
    divider(ax, y+0.10, 15, '4 — Normalisation et persistance')
    note(ax, y-0.05, '    Normalisation UTF-8, espaces, CRLF → LF')
    arrow(ax, xs, 2, 4, y-0.25, 'INSERT extractions  (normalized_text, structure)'); y -= s+0.25
    arrow(ax, xs, 2, 4, y, 'UPDATE  status = extracted  (100 %)'); y -= s
    seq_header(ax, "Diagramme de séquence — Sprint 1 : Téléverser et extraire un contrat", 15)
    save(fig, 'seq_sprint1.png')

def seq_sprint2():
    parts = ['Worker\nCelery', 'Language\nDetector', 'Clause\nSegmenter',
             'Entity\nExtractor', 'Clause\nClassifier', 'PostgreSQL']
    fig, ax, xs = seq_fig(parts, w=16, h=10)
    y, s = 8.30, 0.57
    note(ax, y+0.06, '← Déclenché automatiquement après extraction réussie')
    divider(ax, y+0.05, 16, '1 — Détection de la langue')
    arrow(ax, xs, 0, 1, y, 'detect(normalized_text)'); y -= s
    arrow(ax, xs, 1, 0, y, '"fr" / "ar" / "en"', ret=True); y -= s
    divider(ax, y+0.06, 16, '2 — Segmentation en clauses (3 stratégies)')
    arrow(ax, xs, 0, 2, y, 'segment(text, structure_json)'); y -= s
    arrow(ax, xs, 2, 0, y, '[ClauseSegment × N]  (text, start_char, end_char)', ret=True); y -= s
    divider(ax, y+0.06, 16, '3 — Boucle sur chaque clause')
    arrow(ax, xs, 0, 3, y, 'extract_entities(clause)'); y -= s
    arrow(ax, xs, 3, 0, y, '[Entity]  (PARTY, ROLE, DURATION, LAW_REFERENCE…)', ret=True); y -= s
    arrow(ax, xs, 0, 4, y, 'classify(clause_text)'); y -= s
    arrow(ax, xs, 4, 0, y, '{ labels, compliance_flags, confidence }', ret=True); y -= s
    divider(ax, y+0.06, 16, '4 — Persistance')
    arrow(ax, xs, 0, 5, y, 'INSERT nlp_analyses  (clauses_json, entities_json)'); y -= s
    arrow(ax, xs, 0, 5, y, 'UPDATE  status = analyzed  (100 %)'); y -= s
    seq_header(ax, "Diagramme de séquence — Sprint 2 : Analyser les clauses NLP", 16)
    save(fig, 'seq_sprint2.png')

def seq_sprint3():
    parts = ['Worker\nCelery', 'Rule\nEngine', 'Compliance\nScorer', 'PostgreSQL']
    fig, ax, xs = seq_fig(parts, w=14, h=10)
    y, s = 8.30, 0.60
    note(ax, y+0.06, '← Déclenché automatiquement après analyse NLP réussie')
    divider(ax, y+0.04, 14, '1 — Chargement des règles')
    arrow(ax, xs, 0, 1, y, 'load_rules()  →  44 règles JSON (LNPDP, GDPR, ISO27001, ISO9001)'); y -= s
    divider(ax, y+0.06, 14, '2 — Détermination des référentiels actifs')
    arrow(ax, xs, 0, 1, y, 'determine_active_frameworks(clauses)'); y -= s
    arrow(ax, xs, 1, 0, y, '[LNPDP, GDPR, ISO27001]', ret=True); y -= s
    divider(ax, y+0.06, 14, '3 — Correspondance règles ↔ clauses')
    arrow(ax, xs, 0, 1, y, 'evaluate(clauses)'); y -= s
    arrow(ax, xs, 1, 0, y, 'violations[]  +  missing_clauses[]', ret=True); y -= s
    divider(ax, y+0.06, 14, '4 — Calcul du score de conformité')
    arrow(ax, xs, 0, 2, y, 'compute_scores(violations, active_frameworks)'); y -= s
    note(ax, y-0.04, '    score(F) = 100 − Σ w(sévérité)   |   score global = Σ score(F)×weight(F)')
    arrow(ax, xs, 2, 0, y-0.24, '{ global_score, per_framework_scores, litigation_risk }', ret=True); y -= s+0.24
    divider(ax, y+0.06, 14, '5 — Persistance')
    arrow(ax, xs, 0, 3, y, 'INSERT evaluations  (global_score, violations_json, missing_clauses_json)'); y -= s
    arrow(ax, xs, 0, 3, y, 'UPDATE  status = evaluated  (100 %)'); y -= s
    seq_header(ax, "Diagramme de séquence — Sprint 3 : Évaluer la conformité réglementaire", 14)
    save(fig, 'seq_sprint3.png')

def seq_sprint4():
    parts = ['Worker\nCelery', 'Recommender', 'Template\nLibrary', 'PostgreSQL']
    fig, ax, xs = seq_fig(parts, w=14, h=10)
    y, s = 8.30, 0.60
    note(ax, y+0.06, '← Déclenché automatiquement après évaluation réussie')
    divider(ax, y+0.04, 14, '1 — Tri des violations par sévérité')
    arrow(ax, xs, 0, 1, y, 'build_recommendations(violations, clauses)'); y -= s
    divider(ax, y+0.06, 14, '2 — Boucle sur chaque violation')
    arrow(ax, xs, 1, 2, y, 'lookup_template(rule_id)'); y -= s
    arrow(ax, xs, 2, 1, y, 'template  ou  None', ret=True); y -= s
    note(ax, y+0.04, '    Si template trouvé → slot-filling depuis entités NLP   |   sinon → fallback générique')
    arrow(ax, xs, 1, 1, y-0.20, 'slot_filling( {RETENTION_PERIOD} → entité DURATION )'); y -= s+0.10
    note(ax, y+0.04, '    generated_by = "template_v1"  ou  "fallback_v1"')
    arrow(ax, xs, 1, 0, y-0.14, '[Recommendation × N]  triées par priorité', ret=True); y -= s+0.14
    divider(ax, y+0.06, 14, '3 — Persistance')
    arrow(ax, xs, 0, 3, y, 'DELETE recommendations WHERE document_id = X  (idempotence)'); y -= s
    arrow(ax, xs, 0, 3, y, 'INSERT recommendations  (N lignes)'); y -= s
    arrow(ax, xs, 0, 3, y, 'UPDATE  status = complete,  finished_at = NOW()'); y -= s
    seq_header(ax, "Diagramme de séquence — Sprint 4 : Générer des recommandations", 14)
    save(fig, 'seq_sprint4.png')

# ════════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("Generating use case diagrams...")
    uc_sprint1(); uc_sprint2(); uc_sprint3(); uc_sprint4()
    print("Generating sequence diagrams...")
    seq_sprint1(); seq_sprint2(); seq_sprint3(); seq_sprint4()
    print(f"\nDone! 8 diagrams saved to {OUT}")
