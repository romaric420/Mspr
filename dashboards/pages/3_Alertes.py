"""
Page Alertes - tableau priorise et analyse transverse.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Alertes", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALERTS_PATH = PROJECT_ROOT / "data" / "gold" / "alerts.parquet"

st.title("Systeme d'alertes operationnelles")
st.caption("Synthese transverse des alertes sur le perimetre MECHA")

if not ALERTS_PATH.exists():
    st.error("Alertes non trouvees. Executer le notebook 08.")
    st.stop()

df = pd.read_parquet(ALERTS_PATH)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# ---------- Filtres ----------
st.sidebar.title("Filtres")

priorites = st.sidebar.multiselect(
    "Priorites",
    ["critique", "majeur", "mineur"],
    default=["critique", "majeur", "mineur"],
)

usines = st.sidebar.multiselect(
    "Usines", sorted(df["usine"].unique()), default=sorted(df["usine"].unique())
)

codes = st.sidebar.multiselect(
    "Types d'alerte", sorted(df["code"].unique()), default=sorted(df["code"].unique())
)

df_f = df[
    df["priorite"].isin(priorites)
    & df["usine"].isin(usines)
    & df["code"].isin(codes)
]

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Alertes totales", len(df_f))
c2.metric("Critiques", (df_f["priorite"] == "critique").sum())
c3.metric("Majeures", (df_f["priorite"] == "majeur").sum())
c4.metric("Mineures", (df_f["priorite"] == "mineur").sum())

st.divider()

# ---------- Visualisations ----------
if len(df_f):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Chronologie")
        colors = {"critique": "#e74c3c", "majeur": "#f39c12", "mineur": "#f1c40f"}
        fig = px.scatter(
            df_f, x="timestamp", y="priorite", color="priorite",
            color_discrete_map=colors, hover_data=["code", "message", "usine"]
        )
        fig.update_traces(marker=dict(size=10, opacity=0.7))
        fig.update_layout(height=350, legend_title="")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Repartition par usine")
        pivot = df_f.groupby(["usine", "priorite"]).size().unstack(fill_value=0)
        pivot = pivot.reindex(columns=["critique", "majeur", "mineur"], fill_value=0)
        fig = px.bar(
            pivot, barmode="stack",
            color_discrete_sequence=["#e74c3c", "#f39c12", "#f1c40f"],
        )
        fig.update_layout(height=350, xaxis_title="", yaxis_title="Alertes")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Distribution par type")
    cnt = df_f["code"].value_counts().reset_index()
    cnt.columns = ["code", "count"]
    fig = px.bar(cnt, x="count", y="code", orientation="h", color="code")
    fig.update_layout(height=350, yaxis={"categoryorder": "total ascending"},
                      showlegend=False, xaxis_title="Nombre d'alertes", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---------- Tableau ----------
    st.subheader("Tableau detaille")
    st.caption("Trie du plus recent au plus ancien. Cliquer sur les en-tetes pour trier.")

    display = df_f.sort_values("timestamp", ascending=False)[
        ["timestamp", "usine", "priorite", "code", "message", "valeur", "seuil"]
    ]

    def color_prio(val):
        c = {"critique": "#fecaca", "majeur": "#fed7aa", "mineur": "#fef08a"}.get(val, "")
        return f"background-color: {c}" if c else ""

    st.dataframe(
        display.style.applymap(color_prio, subset=["priorite"]),
        use_container_width=True, hide_index=True, height=500,
    )

    # ---------- Export ----------
    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Exporter en CSV",
        csv,
        f"alertes_mecha_{pd.Timestamp.now():%Y%m%d}.csv",
        "text/csv",
    )
else:
    st.success("Aucune alerte sur les filtres selectionnes.")
