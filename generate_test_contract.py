"""
Generates a realistic French contract PDF for testing Agent 2.
Covers all 12 clause types so the model has something to classify.

Usage:
    .venv\Scripts\python generate_test_contract.py
Output:
    test_contract_fr.pdf
"""

from fpdf import FPDF, XPos, YPos

OUT_FILE = "test_contract_fr.pdf"

CONTRACT_TEXT = {
    "title": "CONTRAT DE PRESTATION DE SERVICES INFORMATIQUES",
    "subtitle": "ET DE TRAITEMENT DE DONNEES PERSONNELLES",
    "parties": (
        "Entre les soussignes :\n\n"
        "TECH SOLUTIONS SARL, societe a responsabilite limitee au capital de 50 000 TND, "
        "immatriculee au Registre du Commerce de Tunis sous le numero B123456789, "
        "dont le siege social est sis au 45 Avenue Habib Bourguiba, 1000 Tunis, Tunisie, "
        "representee par Monsieur Ahmed Ben Salah, Directeur General,\n"
        "ci-apres designee le \"Prestataire\",\n\n"
        "ET\n\n"
        "BIAT SA (Banque Internationale Arabe de Tunisie), societe anonyme au capital de "
        "200 000 000 TND, immatriculee sous le numero C987654321, dont le siege social "
        "est sis au 70-72 Avenue Habib Bourguiba, 1080 Tunis, Tunisie, "
        "representee par Madame Sonia Mabrouk, Directrice des Systemes d'Information,\n"
        "ci-apres designee le \"Client\".\n\n"
        "Ensemble designes les \"Parties\"."
    ),
    "sections": [
        {
            "title": "Article 1 - Definitions",
            "text": (
                "Au sens du present contrat, les termes suivants ont la signification ci-apres indiquee :\n\n"
                "\"Donnees Personnelles\" : toute information relative a une personne physique identifiee "
                "ou identifiable, au sens de la loi tunisienne n 2004-63 du 27 juillet 2004 portant sur "
                "la protection des donnees a caractere personnel (LNPDP) et du Reglement General sur la "
                "Protection des Donnees (RGPD).\n\n"
                "\"Traitement\" : toute operation ou ensemble d operations effectuees ou non a l aide de "
                "procedes automatises, appliquees a des donnees personnelles.\n\n"
                "\"Responsable du Traitement\" : la personne physique ou morale qui determine les finalites "
                "et les moyens du traitement des donnees personnelles.\n\n"
                "\"Sous-traitant\" : la personne physique ou morale qui traite des donnees personnelles "
                "pour le compte du Responsable du Traitement.\n\n"
                "\"Services\" : l ensemble des prestations informatiques fournies par le Prestataire au "
                "Client, telles que definies a l article 2 du present contrat."
            ),
        },
        {
            "title": "Article 2 - Objet et Obligations du Prestataire",
            "text": (
                "Le present contrat a pour objet de definir les conditions dans lesquelles le Prestataire "
                "s engage a fournir au Client des services de developpement logiciel, de maintenance "
                "informatique et de traitement de donnees.\n\n"
                "Le Prestataire s engage a :\n"
                "- Fournir les Services conformement aux specifications techniques annexees au present contrat ;\n"
                "- Respecter les delais convenus entre les Parties ;\n"
                "- Mettre a disposition du Client une equipe technique qualifiee ;\n"
                "- Informer le Client de tout incident susceptible d affecter la qualite des Services ;\n"
                "- Se conformer a toutes les obligations legales et reglementaires applicables.\n\n"
                "Le Client s engage a :\n"
                "- Fournir au Prestataire toutes les informations necessaires a l execution des Services ;\n"
                "- Payer les honoraires dans les delais stipules a l article 5 ;\n"
                "- Cooperer de bonne foi avec le Prestataire."
            ),
        },
        {
            "title": "Article 3 - Duree et Resiliation",
            "text": (
                "Le present contrat est conclu pour une duree determinee de vingt-quatre (24) mois "
                "a compter de la date de sa signature, soit jusqu au 20 avril 2028.\n\n"
                "Il pourra etre renouvele par tacite reconduction pour des periodes successives de "
                "douze (12) mois, sauf denonciation par l une des Parties par lettre recommandee avec "
                "accuse de reception, adressee au moins soixante (60) jours avant l echeance.\n\n"
                "Chacune des Parties pourra resilier le present contrat avant son terme en cas de "
                "manquement grave de l autre Partie a ses obligations, apres mise en demeure restee "
                "sans effet pendant trente (30) jours.\n\n"
                "En cas de resiliation anticipee pour motif legitime, le Prestataire devra assurer "
                "une periode de transition de trois (3) mois afin de garantir la continuite des services."
            ),
        },
        {
            "title": "Article 4 - Confidentialite",
            "text": (
                "Chaque Partie s engage a garder strictement confidentiels tous les documents, "
                "informations, donnees techniques, commerciales ou financieres communiquees par "
                "l autre Partie dans le cadre de l execution du present contrat.\n\n"
                "Cette obligation de confidentialite s applique a toute information qualifiee de "
                "confidentielle par la Partie divulgatrice, qu elle soit communiquee oralement, "
                "par ecrit ou sous toute autre forme.\n\n"
                "Les Parties s engagent a ne pas divulguer ces informations confidentielles a des "
                "tiers sans l accord prealable et ecrit de l autre Partie, et a n utiliser ces "
                "informations qu aux fins d execution du present contrat.\n\n"
                "Cette obligation de non-divulgation survivra a la resiliation ou a l expiration "
                "du present contrat pour une duree de cinq (5) ans."
            ),
        },
        {
            "title": "Article 5 - Remuneration et Conditions de Paiement",
            "text": (
                "En contrepartie des Services fournis, le Client versera au Prestataire une "
                "remuneration mensuelle forfaitaire de quinze mille dinars tunisiens (15 000 TND HT), "
                "soit cent quatre-vingt mille dinars (180 000 TND HT) par an.\n\n"
                "Les honoraires sont payables dans un delai de trente (30) jours a compter de la "
                "date d emission de chaque facture.\n\n"
                "Tout retard de paiement donnera lieu, de plein droit et sans mise en demeure "
                "prealable, a des penalites de retard au taux de 1,5% par mois de retard.\n\n"
                "Le Prestataire se reserve le droit de reviser ses tarifs une fois par an, "
                "sous reserve d un preavis de deux (2) mois adresse par ecrit au Client.\n\n"
                "Les prix sont exprimes hors taxes. La TVA applicable sera ajoutee au taux en "
                "vigueur au moment de la facturation, soit 19% a la date de signature."
            ),
        },
        {
            "title": "Article 6 - Propriete Intellectuelle",
            "text": (
                "Les livrables developpes specifiquement pour le Client dans le cadre du present "
                "contrat seront la propriete exclusive du Client des leur paiement integral.\n\n"
                "Le Prestataire conserve la propriete intellectuelle de ses outils, methodologies, "
                "frameworks et codes generiques pre-existants. Il concede au Client une licence "
                "d utilisation non exclusive, non transferable et non sous-licenciable sur ces "
                "elements, limitee a l usage interne du Client.\n\n"
                "Toute reproduction, modification, adaptation ou distribution des livrables "
                "par le Client au profit de tiers est strictement interdite sans accord "
                "prealable ecrit du Prestataire.\n\n"
                "Le Prestataire garantit que les livrables fournis ne portent pas atteinte "
                "aux droits de propriete intellectuelle de tiers."
            ),
        },
        {
            "title": "Article 7 - Traitement des Donnees Personnelles",
            "text": (
                "Dans le cadre de l execution des Services, le Prestataire sera amene a traiter "
                "des donnees personnelles pour le compte du Client, agissant en qualite de "
                "Responsable du Traitement au sens de la loi tunisienne n 2004-63 et du RGPD.\n\n"
                "Le Prestataire s engage a traiter les donnees personnelles uniquement sur "
                "instructions documentees du Client, et conformement aux finalites suivantes : "
                "gestion des comptes clients, traitement des transactions bancaires et "
                "prevention de la fraude.\n\n"
                "Les categories de donnees traitees incluent : identite civile, coordonnees "
                "bancaires, historique des transactions et donnees de connexion.\n\n"
                "Le Prestataire s engage a mettre en oeuvre les mesures de securite techniques "
                "et organisationnelles appropriees, notamment le chiffrement des donnees en "
                "transit et au repos, la pseudonymisation des donnees sensibles, et la gestion "
                "des acces autorises selon le principe du moindre privilege.\n\n"
                "Toute sous-traitance ulterieure des operations de traitement est soumise a "
                "l autorisation prealable et ecrite du Client.\n\n"
                "En cas de violation de donnees personnelles, le Prestataire s engage a "
                "notifier le Client dans les 72 heures suivant la detection de l incident."
            ),
        },
        {
            "title": "Article 8 - Responsabilite et Garanties",
            "text": (
                "Le Prestataire garantit que les Services seront fournis conformement aux "
                "regles de l art et aux specifications contractuelles. En cas de non-conformite, "
                "le Prestataire s engage a corriger les defauts signales dans un delai de "
                "quinze (15) jours ouvrables.\n\n"
                "La responsabilite du Prestataire est limitee aux dommages directs et previsibles. "
                "En aucun cas le Prestataire ne saurait etre tenu responsable des dommages "
                "indirects, pertes d exploitation, manque a gagner ou atteinte a l image.\n\n"
                "La responsabilite totale du Prestataire au titre du present contrat est plafonnee "
                "a un montant equivalent aux honoraires verses par le Client au cours des douze "
                "(12) derniers mois precedant la survenance du dommage.\n\n"
                "Le Prestataire souscrit et maintient pendant toute la duree du contrat une "
                "assurance responsabilite civile professionnelle aupres d une compagnie "
                "d assurance agreee."
            ),
        },
        {
            "title": "Article 9 - Force Majeure",
            "text": (
                "Aucune des Parties ne sera tenue responsable de l inexecution ou du retard "
                "dans l execution de ses obligations contractuelles resultant d un evenement "
                "de force majeure, c est-a-dire tout evenement imprévisible, irresistible et "
                "exterieur aux Parties, au sens de l article 283 du Code des Obligations "
                "et des Contrats tunisien.\n\n"
                "Sont notamment consideres comme cas de force majeure : catastrophes naturelles, "
                "guerres, actes terroristes, pandemies, greves generales, pannes de reseaux "
                "de communication au niveau national, et decisions gouvernementales imprevues.\n\n"
                "La Partie invoquant la force majeure devra notifier l autre Partie dans les "
                "quarante-huit (48) heures suivant la survenance de l evenement, par tout moyen "
                "ecrit, et fournir les justificatifs necessaires.\n\n"
                "Si l evenement de force majeure se prolonge au-dela de soixante (60) jours "
                "consecutifs, chacune des Parties pourra resilier le present contrat sans "
                "indemnite de part et d autre."
            ),
        },
        {
            "title": "Article 10 - Penalites en cas de Manquement",
            "text": (
                "En cas de non-respect des delais de livraison imputes au Prestataire, "
                "des penalites de retard seront applicables de plein droit a raison de "
                "0,5% du montant mensuel des honoraires par jour ouvrable de retard, "
                "dans la limite de 10% du montant total du contrat.\n\n"
                "En cas de violation de l obligation de confidentialite par le Prestataire, "
                "le Client pourra reclamer des dommages-interets forfaitaires d un montant "
                "de cinquante mille dinars (50 000 TND) par incident documente, sans "
                "prejudice de tout recours judiciaire complementaire.\n\n"
                "Les penalites prevues au present article constituent une evaluation "
                "forfaitaire et definitive du prejudice subi, et ne peuvent se cumuler "
                "avec d autres indemnisations pour le meme manquement."
            ),
        },
        {
            "title": "Article 11 - Droit Applicable et Reglement des Litiges",
            "text": (
                "Le present contrat est regi et interprete conformement au droit tunisien, "
                "notamment le Code des Obligations et des Contrats (COC) promulgue par "
                "la loi du 15 decembre 1906 et ses modifications ulterieures.\n\n"
                "En cas de differend entre les Parties relatif a l interpretation, "
                "l execution ou la resiliation du present contrat, les Parties s engagent "
                "a tenter de resoudre ce differend a l amiable dans un delai de trente "
                "(30) jours a compter de la notification du differend par la partie la "
                "plus diligente.\n\n"
                "A defaut d accord amiable dans ce delai, le differend sera soumis a "
                "l arbitrage du Centre d Arbitrage et de Mediation de Tunis (CAMT), "
                "conformement a son reglement d arbitrage en vigueur.\n\n"
                "La juridiction competente pour tout litige non soumis a arbitrage sera "
                "le Tribunal de Premiere Instance de Tunis."
            ),
        },
        {
            "title": "Article 12 - Dispositions Generales",
            "text": (
                "Le present contrat constitue l integralite de l accord entre les Parties "
                "et annule et remplace tous les accords, negociations et representations "
                "anterieurs relatifs a son objet.\n\n"
                "Toute modification du present contrat devra faire l objet d un avenant "
                "ecrit signe par les representants dument habilites des deux Parties.\n\n"
                "Si une clause du present contrat est declaree nulle ou inapplicable, "
                "les autres clauses demeurent en vigueur et la clause nulle sera "
                "remplacee par une clause valide ayant l effet le plus proche.\n\n"
                "Le present contrat est etabli en deux (2) exemplaires originaux, "
                "un pour chaque Partie, ayant egale valeur juridique.\n\n"
                "Fait a Tunis, le 20 avril 2026.\n\n"
                "Pour TECH SOLUTIONS SARL                    Pour BIAT SA\n"
                "M. Ahmed Ben Salah                          Mme Sonia Mabrouk\n"
                "Directeur General                           Directrice des SI\n"
                "Signature et cachet                         Signature et cachet"
            ),
        },
    ],
}


class ContractPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, "CONFIDENTIEL - Contrat de Prestation de Services", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    def add_title(self, title: str, subtitle: str) -> None:
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(20, 40, 80)
        self.ln(4)
        self.cell(0, 8, title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, subtitle, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        self.set_draw_color(20, 40, 80)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)

    def add_section_title(self, title: str) -> None:
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(20, 40, 80)
        self.set_fill_color(235, 240, 250)
        self.cell(0, 8, title, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def add_body(self, text: str) -> None:
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5, text)
        self.ln(4)

    def add_parties(self, text: str) -> None:
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        self.set_fill_color(248, 248, 252)
        self.multi_cell(0, 5, text, fill=True)
        self.ln(4)


def generate():
    pdf = ContractPDF()
    pdf.set_margins(20, 25, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    data = CONTRACT_TEXT
    pdf.add_title(data["title"], data["subtitle"])
    pdf.add_parties(data["parties"])

    for section in data["sections"]:
        pdf.add_section_title(section["title"])
        pdf.add_body(section["text"])

    pdf.output(OUT_FILE)
    print(f"Contract generated: {OUT_FILE}")
    print(f"Pages: {pdf.page}")
    print(f"Sections: {len(data['sections'])}")
    print("Clause types covered:")
    print("  - Article 1: definition")
    print("  - Article 2: obligation")
    print("  - Article 3: termination")
    print("  - Article 4: confidentiality")
    print("  - Article 5: payment, penalty")
    print("  - Article 6: ip_rights")
    print("  - Article 7: data_processing (LNPDP + GDPR flags)")
    print("  - Article 8: liability, warranty")
    print("  - Article 9: force_majeure")
    print("  - Article 10: penalty")
    print("  - Article 11: dispute_resolution")
    print("  - Article 12: obligation")


if __name__ == "__main__":
    generate()
