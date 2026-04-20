"""
Page Qualite des donnees - rapports bronze / silver.
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Qualite des donnees", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUALITY_DIR = PROJECT_ROOT / "reports" / "quality"

st.title("Qualite des donnees")
st.caption("Rapport bronze vers silver : detection et correction des defauts")

if not QUALITY_DIR.exists():
    st.error("Rapports non trouves. Executer le notebook 03.")
    st.stop()

files = sorted(QUALITY_DIR.glob("*_quality.json"))
if not files:
    st.warning("Aucun rapport JSON trouve.")
    st.stop()

# ---------- Choix usine ----------
usine = st.selectbox(
    "Usine", [f.stem.replace("_quality", "") for f in files]
)

report = json.loads((QUALITY_DIR / f"{usine}_quality.json").read_text())

# ---------- Comparatif global ----------
st.subheader("Comparatif avant / apres nettoyage")

comp = pd.DataFrame(
    {
        "Etape": ["Avant", "Apres"],
        "Lignes": [report["avant"]["n_rows"], report["apres"]["n_rows"]],
        "Doublons": [
            report["avant"]["duplicates_full"],
            report["apres"]["duplicates_full"],
        ],
        "Missing total": [
            report["avant"]["missing_total"],
            report["apres"]["missing_total"],
        ],
        "Completude (%)": [
            report["avant"]["completeness_pct"],
            report["apres"]["completeness_pct"],
        ],
    }
)
st.dataframe(comp, use_container_width=True, hide_index=True)

# ---------- Graphes ----------
c1, c2 = st.columns(2)

with c1:
    fig = px.bar(
        comp, x="Etape", y="Completude (%)", color="Etape",
        title="Evolution de la completude",
        range_y=[95, 100.5],
        color_discrete_map={"Avant": "#e74c3c", "Apres": "#2ecc71"},
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = px.bar(
        comp, x="Etape",
        y=["Missing total", "Doublons"], barmode="group",
        title="Defauts detectes",
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- Detail par colonne ----------
st.subheader("Detail des valeurs manquantes par colonne")

avant_cols = report["avant"]["missing_per_col"]
apres_cols = report["apres"]["missing_per_col"]

all_cols = sorted(set(list(avant_cols.keys()) + list(apres_cols.keys())))

miss = pd.DataFrame(
    {
        "Colonne": all_cols,
        "Avant": [avant_cols.get(c, 0) for c in all_cols],
        "Apres": [apres_cols.get(c, 0) for c in all_cols],
    }
)
miss = miss[(miss["Avant"] > 0) | (miss["Apres"] > 0)]

if len(miss):
    fig = px.bar(
        miss, x="Colonne", y=["Avant", "Apres"], barmode="group",
        color_discrete_map={"Avant": "#e74c3c", "Apres": "#2ecc71"},
    )
    fig.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Pas de detail par colonne disponible.")

# ---------- Synthese ----------
st.divider()
st.success(
    f"Resultat final : {report['apres']['n_rows']} lignes propres, "
    f"completude {report['apres']['completeness_pct']}% "
    f"(vs {report['avant']['completeness_pct']}% avant nettoyage)."
)

st.markdown(
    """
### Regles de nettoyage appliquees (notebook 03)

1. Valeurs texte dans colonnes numeriques (`"N/A"`, `"null"`, `"-"`) converties en NaN
2. Valeurs sentinelles (-1, 999.9, 99999) converties en NaN
3. Normalisation `Type` (strip + upper) supprime les variantes d'encodage
4. Dedoublonnage sur la cle metier `(UDI, timestamp)`
5. Clipping IQR (k=3) sur les outliers extremes
6. Imputation mediane des valeurs manquantes (robuste aux outliers)
7. Re-typage strict post-correction (int, float)
8. Correction des labels contradictoires (`Machine failure = 1` sans sous-type)
"""
)
