# MECHA - Proof of Concept Pilotage Industriel

**Certification professionnelle RNCP 35584 - Expert en Informatique et Système d'Information (Niveau 7)**
**Bloc de compétences 3 : Piloter l'informatique décisionnelle d'un S.I. (Big Data & BI)**
**Mise en Situation Professionnelle Reconstituée - TPRE831**

---

## Table des matières

1. [Contexte métier](#1-contexte-métier)
2. [Objectifs du PoC](#2-objectifs-du-poc)
3. [Architecture technique](#3-architecture-technique)
4. [Jeu de données](#4-jeu-de-données)
5. [Stack technique](#5-stack-technique)
6. [Structure du projet](#6-structure-du-projet)
7. [Installation](#7-installation)
8. [Exécution du pipeline](#8-exécution-du-pipeline)
9. [Dashboard](#9-dashboard)
10. [Parcours des notebooks](#10-parcours-des-notebooks)
11. [Résultats](#11-résultats)
12. [Livrables MSPR](#12-livrables-mspr)
13. [Couverture de la grille de compétences](#13-couverture-de-la-grille-de-compétences)
14. [Équipe projet](#14-équipe-projet)
15. [Licence](#15-licence)

---

## 1. Contexte métier

MECHA est une entreprise industrielle (fictive) spécialisée dans la fabrication discrète de pièces mécaniques de haute précision, destinées principalement aux secteurs aéronautique et automobile. Elle exploite cinq sites de production (trois en France, deux en Espagne) équipés de lignes automatisées comprenant notamment des centres d'usinage CNC.

La Direction générale souhaite engager un programme de modernisation industrielle (Industrie 4.0) visant à :

- Consolider le pilotage des cinq usines via des tableaux de bord temps réel,
- Renforcer la maîtrise qualité et détecter les dérives de production plus tôt,
- Préparer l'intégration progressive de modèles d'Intelligence Artificielle pour la maintenance prédictive et l'aide à la décision.

Le présent projet constitue un **Proof of Concept** portant sur un périmètre restreint de deux usines (FR-01 et ES-01), destiné à valider la faisabilité technique et la valeur métier d'un tel dispositif avant un déploiement à plus grande échelle.

---

## 2. Objectifs du PoC

Le projet doit démontrer la capacité à :

1. Collecter et structurer les données industrielles issues de capteurs machines,
2. Construire un référentiel de données cohérent et un entrepôt décisionnel,
3. Garantir la qualité, la traçabilité et la sécurité des données,
4. Restituer l'information sous forme de tableaux de bord BI à destination des directions métiers,
5. Intégrer un système d'alertes opérationnelles priorisées,
6. Évaluer la pertinence d'approches de Machine Learning pour la détection de dérives qualité et la prédiction de défaillances machine.

---

## 3. Architecture technique

### 3.1 Architecture en médaille (bronze / silver / gold)

```
data/
├── raw/       Source brute immuable (CSV AI4I 2020 + pointeur DVC)
├── bronze/    Données ingérées et horodatées, découpées par usine
├── silver/    Données nettoyées, typées et validées
└── gold/      Entrepôt multidimensionnel (DuckDB) + artefacts ML
```

Cette séparation en couches garantit :

- Une traçabilité complète de la donnée de la source à la restitution,
- La possibilité de rejouer toute transformation sans corrompre la source,
- Une séparation nette des responsabilités entre ingestion, préparation et exposition.

### 3.2 Architecture BI en trois couches

| Couche | Rôle | Outils |
|---|---|---|
| 1 - Collecte | Ingestion des données brutes | Python, Parquet, DVC |
| 2 - Modélisation et stockage | Nettoyage, typage, entrepôt multidimensionnel | Pandas, Pandera, DuckDB |
| 3 - Restitution | Dashboards et aide à la décision | Streamlit, Plotly, MLflow |

### 3.3 Modèle multidimensionnel en étoile

```
          dim_usine
              |
  dim_temps - fact_production - dim_produit
              |
          dim_machine
```

Choix de l'étoile plutôt que du flocon pour sa simplicité de requêtage, sa performance sur DuckDB (stockage colonnaire) et sa lisibilité pour les utilisateurs métiers.

---

## 4. Jeu de données

**AI4I 2020 Predictive Maintenance Dataset** (Stephan Matzka, 2020)

- Source : UCI Machine Learning Repository (id 601)
- Licence : Creative Commons Attribution 4.0 International (CC BY 4.0)
- 10 000 observations issues d'une fraiseuse CNC synthétique
- 8 variables explicatives : identifiant pièce, gamme produit (L/M/H), température air, température process, vitesse de rotation, couple, usure outil
- 1 cible principale (défaillance machine) et 5 cibles secondaires (TWF, HDF, PWF, OSF, RNF) correspondant aux types de défaillance (usure outil, chaleur, puissance, surcharge, aléatoire)

### Enrichissement pour le PoC

Le dataset brut étant jugé trop propre au regard d'une remontée SCADA/MES réelle, il a été enrichi de défauts réalistes conformément aux autorisations du cahier des charges (§II, page 8) :

| Type de défaut | Volume | Cause industrielle simulée |
|---|---|---|
| Valeurs manquantes | ~2.5 % par capteur | Capteur en panne, perte réseau |
| Doublons | 70 lignes | Retransmissions SCADA |
| Valeurs texte (`"N/A"`, `"null"`, etc.) | ~60 | Mauvais parsing JSON/XML |
| Valeurs sentinelles (-1, 999.9, 99999) | ~60 | Codes d'erreur capteurs |
| Outliers extrêmes | ~40 | Pics électriques |
| Encodage `Type` incohérent | ~50 | Saisie manuelle MES |
| Labels contradictoires | 15 | Erreur saisie opérateur |

Le dataset est par ailleurs découpé en deux sous-ensembles représentant les usines FR-01 et ES-01, avec un léger décalage contrôlé des paramètres sur ES-01 (usure outil +8 min, bruit capteur additionnel) afin de simuler une dérive inter-site.

---

## 5. Stack technique

| Couche | Outil | Justification |
|---|---|---|
| Gestion de projet Python | uv | Gestion unifiée environnement et dépendances, reproductibilité via `uv.lock` |
| Versioning des données | DVC | Traçabilité des jeux de données, compatible git |
| Validation qualité | Pandera | Schémas typés, checks automatisés |
| Entrepôt analytique | DuckDB | Base OLAP embarquée, SQL standard, stockage colonnaire |
| Machine Learning | scikit-learn, XGBoost | Modèles baseline et boosting sur données tabulaires |
| Rééquilibrage de classe | imbalanced-learn, `class_weight` | Gestion du déséquilibre 3.4 % de pannes |
| Suivi d'expériences | MLflow | Standard industriel pour tracking et model registry |
| Restitution BI | Streamlit, Plotly | Dashboards interactifs multi-pages |
| Tests | pytest, ruff | Qualité logicielle |
| CI/CD | GitHub Actions | Automatisation des tests |

---

## 6. Structure du projet

```
mecha-poc/
├── data/
│   ├── raw/              Source brute (versionnée par DVC)
│   ├── bronze/           Parquet par usine (FR-01, ES-01)
│   ├── silver/           Parquet nettoyés
│   └── gold/             Entrepôt DuckDB, KPIs, modèle ML, alertes
├── notebooks/            Parcours pédagogique (01 à 08)
├── dashboards/           Application Streamlit multi-pages
│   ├── home.py           Vue Groupe
│   └── pages/            Vues Usine, IA, Alertes, Qualité
├── reports/
│   ├── quality/          Rapports JSON avant/après nettoyage
│   ├── figures/          Figures exportées
│   └── livrables/        Livrables MSPR
├── docs/                 Documentation projet (mapping compétences)
├── configs/              Paramètres centralisés
├── tests/                Tests unitaires
├── .github/workflows/    Pipelines CI
├── pyproject.toml        Dépendances (uv)
├── uv.lock               Lockfile reproductibilité
├── .gitignore
├── .dvcignore
└── README.md
```

---

## 7. Installation

### 7.1 Prérequis

- Linux (ou WSL2 sous Windows)
- Python 3.12
- Git

### 7.2 Installation d'uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Relancer le terminal ou sourcer le profil :

```bash
source ~/.bashrc
```

### 7.3 Clonage et installation des dépendances

```bash
git clone <url-du-repo>
cd mecha-poc
uv sync --extra dev
```

### 7.4 Récupération des données

Le dataset brut est versionné via DVC (le fichier réel n'est pas dans git). Deux options :

**Option A - Récupération depuis le remote DVC** (si configuré) :

```bash
uv run dvc pull
```

**Option B - Téléchargement manuel** :

Télécharger `ai4i2020.csv` depuis [Kaggle](https://www.kaggle.com/datasets/stephanmatzka/predictive-maintenance-dataset-ai4i-2020) ou [UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), puis le placer dans `data/raw/`.

---

## 8. Exécution du pipeline

Le pipeline complet se déroule en exécutant les notebooks dans l'ordre numérique.

### 8.1 Exécution via Jupyter / VS Code

```bash
uv run jupyter lab
```

Ouvrir le dossier `notebooks/` et exécuter dans l'ordre :

1. `01_exploration_donnees.ipynb`
2. `01bis_tests_statistiques.ipynb`
3. `02_ingestion_bronze.ipynb`
4. `03_qualite_donnees.ipynb`
5. `04_kpis_metiers.ipynb`
6. `05_entrepot_etoile.ipynb`
7. `06_feature_engineering.ipynb`
8. `07_machine_learning.ipynb`
9. `08_alertes.ipynb`

### 8.2 Suivi des expériences MLflow

Dans un terminal séparé :

```bash
uv run mlflow ui --port 5000
```

Ouvrir http://localhost:5000 pour consulter les runs d'entraînement, les métriques et les artefacts.

### 8.3 Tests

```bash
uv run pytest -v
```

---

## 9. Dashboard

### 9.1 Lancement

```bash
uv run streamlit run dashboards/home.py
```

Ouvre http://localhost:8501.

### 9.2 Pages disponibles

| Page | Contenu |
|---|---|
| Vue Groupe (accueil) | KPIs consolidés, TRS, rebut, benchmark inter-usines, typologie des défaillances |
| Vue Usine | Détail par site, alertes des 48 dernières heures, suivi horaire production/qualité/machine |
| IA Prédictif | Benchmark des modèles, prédiction interactive avec jauge de risque |
| Alertes | Tableau priorisé (critique/majeur/mineur), chronologie, export CSV |
| Qualité des données | Comparatif avant/après nettoyage, détail par colonne |

---

## 10. Parcours des notebooks

| N° | Notebook | Objectif | Compétences grille |
|---|---|---|---|
| 01 | Exploration des données | Audit structure, qualité, distributions, corrélations | C1, C5, C8 |
| 01bis | Tests d'hypothèses statistiques | Validation scientifique (Shapiro, Khi², Mann-Whitney, Kruskal, Spearman) | C4, C8 |
| 02 | Ingestion bronze | Split multi-usines, horodatage, écriture Parquet | C3, C1 |
| 03 | Qualité des données | Nettoyage, imputation, rapports avant/après | C8 |
| 04 | KPIs métiers | TRS, rebut, disponibilité, cycle, énergie | C5, C6 |
| 05 | Entrepôt étoile | Modèle multidimensionnel DuckDB | C7, C2 |
| 06 | Feature engineering | Variables physiques et interactions | C4 |
| 07 | Machine Learning | Benchmark 3 modèles avec MLflow, PR-AUC 0.705 | C4 |
| 08 | Système d'alertes | Règles métier + statistique + scoring ML | C5, C4 |

---

## 11. Résultats

### 11.1 Qualité des données

| Indicateur | Bronze | Silver |
|---|---|---|
| Lignes | 10 070 | 10 000 |
| Doublons | 65 | 0 |
| Valeurs manquantes | ~1 250 | 0 |
| Complétude | ~95 % | 100 % |

### 11.2 Modèle Machine Learning

Classe déséquilibrée (3.4 % de pannes), métrique retenue : PR-AUC (Average Precision).

| Modèle | PR-AUC | ROC-AUC | F1 | Precision | Recall |
|---|---|---|---|---|---|
| Logistic Regression | 0.361 | 0.791 | 0.171 | 0.094 | 0.956 |
| Random Forest | 0.636 | 0.962 | 0.580 | 0.438 | 0.853 |
| **XGBoost (retenu)** | **0.705** | **0.965** | **0.696** | **0.600** | **0.824** |

Seuil minimal exigé par la grille MSPR : PR-AUC > 0.5. Seuil dépassé par XGBoost et Random Forest.

### 11.3 Système d'alertes

Trois moteurs combinés :

- Règles métier sur KPIs horaires (rebut, usure outil, température)
- Détection statistique (z-score couple, 3 pannes consécutives)
- Scoring ML (probabilité de défaillance > 30 %)

Priorisation à trois niveaux : critique, majeur, mineur.

---

## 12. Livrables MSPR

Les livrables écrits attendus par le cahier des charges sont regroupés dans `reports/livrables/` :

1. **Note de cadrage** - contexte, SWOT, schéma usine, proposition de tableaux de bord, ROI estimé, planning
2. **Analyse des risques** - risques techniques, organisationnels, réglementaires et mesures de mitigation
3. **Dossier de veille technologique et réglementaire IA** (FR/EN) - technologies, outils, évolutions normatives
4. **Benchmark des solutions IA/BI** - comparatif argumenté des approches (modèles, frameworks, outils BI)
5. **Audit macro des données et diagnostic de maturité data** - cartographie des sources, qualité, prérequis
6. **Note de faisabilité et recommandations** - synthèse décisionnelle pour la Direction générale

Un document complémentaire `docs/mapping_competences.md` établit la correspondance ligne à ligne entre la grille d'évaluation MSPR et les livrables / sections du projet.

---

## 13. Couverture de la grille de compétences

Bloc 3 : Piloter l'informatique décisionnelle d'un S.I. (Big Data & BI)

| Compétence | Preuve dans le projet |
|---|---|
| C1 - Collecter les besoins en données | Note de cadrage, notebook 01, diagrammes de flux |
| C2 - Définir une architecture BI | Architecture en trois couches documentée (README §3) |
| C3 - Définir une stratégie Big Data | Notebook 02, pipeline DVC, stockage Parquet, entrepôt DuckDB |
| C4 - Proposer des modèles statistiques / data science | Notebook 01bis (tests), notebook 07 (ML), PR-AUC = 0.705 |
| C5 - Organiser les sources sous forme de résultats exploitables | Dashboard Streamlit multi-pages |
| C6 - Définir les données de référence | Notebook 04 (KPIs référentiels), dimensions entrepôt |
| C7 - Créer un entrepôt unique | Notebook 05, modèle en étoile DuckDB |
| C8 - Assurer la qualité des données | Notebook 03, Pandera, rapports JSON avant/après |
| C9 - Appliquer les procédures de sécurité / RGPD | Section sécurité de la note de faisabilité |

---

## 14. Équipe projet

À compléter.

---

## 15. Licence

Projet réalisé dans un cadre strictement pédagogique (MSPR EPSI).
Le jeu de données AI4I 2020 est distribué sous licence Creative Commons BY 4.0.