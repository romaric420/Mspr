# Livrables MSPR TPRE831 - Projet MECHA

Dossier de livrables du Proof of Concept MECHA realise dans le cadre de la MSPR TPRE831 (Bloc 3) de la certification RNCP 35584 Expert en Informatique et Systeme d'Information.

## Contenu

| Livrable | Fichier | Description |
|----------|---------|-------------|
| 01 | 01_Note_de_Cadrage.docx | Cadrage strategique du PoC (contexte, SWOT, perimetre, planning, budget, gouvernance) |
| 02 | 02_Analyse_des_Risques.docx | Identification et cotation de 16 risques, matrice P x G, plans de mitigation |
| 03 | 03_Dossier_de_Veille.docx | Veille technologique IA/BI et reglementaire (RGPD, AI Act, EN 9100, ISO 22400, IEC 62443) - volet FR + summary EN |
| 04 | 04_Benchmark_Solutions.docx | Comparatif argumente des solutions data, ML, MLOps, BI |
| 05 | 05_Audit_Donnees.docx | Cartographie sources, qualite, diagnostic maturite DCAM, feuille de route |
| 06 | 06_Note_de_Faisabilite.docx | Synthese decisionnelle pour la Direction, ROI, recommandation Go pilote |

## Equipe projet

- Romaric TCHOFFO
- Emmanuel AMEGA

EPSI - Mastere Expert en Intelligence Artificielle - 2025/2026

## Emplacement recommande dans le depot GitHub

```
MSPR/
└── reports/
    └── livrables/
        ├── 01_Note_de_Cadrage.docx
        ├── 02_Analyse_des_Risques.docx
        ├── 03_Dossier_de_Veille.docx
        ├── 04_Benchmark_Solutions.docx
        ├── 05_Audit_Donnees.docx
        ├── 06_Note_de_Faisabilite.docx
        └── Rapport_Soutenance_MECHA_MSPR.docx (bonus, genere separement)
```

## Commit suggere

```bash
cd ~/MSPR
mkdir -p reports/livrables
# copier les 6 .docx depuis Windows vers ce dossier
git add reports/livrables/*.docx
git commit -m "docs(livrables): add 6 MSPR TPRE831 written deliverables

- 01 Note de cadrage
- 02 Analyse des risques
- 03 Dossier de veille FR/EN
- 04 Benchmark solutions IA/BI
- 05 Audit des donnees et maturite
- 06 Note de faisabilite pour la Direction"
git push
```
