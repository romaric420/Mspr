"""
MECHA - Dashboard BI (home.py)

Page d'accueil : vue consolidee du groupe industriel MECHA.
Lancement : `uv run streamlit run dashboards/home.py`
"""
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ---------- Configuration page ----------
st.set_page_config(
    page_title="MECHA - Pilotage industriel",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Constantes ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "gold" / "mecha.duckdb"
KPIS_JOUR_PATH = PROJECT_ROOT / "data" / "gold" / "kpis_jour.parquet"

# ---------- Style global ----------
st.markdown(
    """
    <style>
    .kpi-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        padding: 20px; border-radius: 12px; color: white; text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .kpi-value { font-size: 2.2rem; font-weight: 700; }
    .kpi-label { font-size: 0.8rem; opacity: 0.85; text-transform: uppercase; letter-spacing: 0.05em; }
    h1, h2, h3 { color: #1e293b; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Data loaders ----------
@st.cache_data(ttl=60)
def load_production() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM v_production").df()
    con.close()
    return df


@st.cache_data(ttl=60)
def load_kpis_jour() -> pd.DataFrame:
    df = pd.read_parquet(KPIS_JOUR_PATH)
    df["jour"] = pd.to_datetime(df["jour"])
    return df


# ---------- Helpers ----------
def kpi_card(label: str, value: str, help_txt: str | None = None):
    st.markdown(
        f"""<div class="kpi-card">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value">{value}</div>
            </div>""",
        unsafe_allow_html=True,
    )
    if help_txt:
        st.caption(help_txt)


# ---------- Guard ----------
if not DB_PATH.exists():
    st.error(
        "Entrepot non trouve. Executer les notebooks 02 a 05 "
        "pour construire `data/gold/mecha.duckdb`."
    )
    st.stop()

if not KPIS_JOUR_PATH.exists():
    st.error("KPIs absents. Executer le notebook 04.")
    st.stop()


# ---------- En-tete ----------
st.title("MECHA - Pilotage industriel")
st.caption(
    "PoC MSPR TPRE831 - Vue consolidee du groupe (perimetre : usines FR-01 et ES-01)"
)

# ---------- Sidebar : filtres ----------
st.sidebar.title("Filtres")
df_prod = load_production()
df_kpis = load_kpis_jour()

usines_dispo = sorted(df_prod["usine"].unique())
usines = st.sidebar.multiselect("Usines", usines_dispo, default=usines_dispo)

gammes_dispo = sorted(df_prod["gamme"].unique())
gammes = st.sidebar.multiselect("Gammes produit", gammes_dispo, default=gammes_dispo)

jours_dispo = sorted(df_kpis["jour"].dt.date.unique())
d_min, d_max = jours_dispo[0], jours_dispo[-1]
date_range = st.sidebar.date_input(
    "Periode", value=(d_min, d_max), min_value=d_min, max_value=d_max
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    d_start, d_end = date_range
else:
    d_start, d_end = d_min, d_max

# ---------- Filtrage ----------
df_k = df_kpis[
    (df_kpis["usine"].isin(usines))
    & (df_kpis["jour"].dt.date >= d_start)
    & (df_kpis["jour"].dt.date <= d_end)
]
df_p = df_prod[df_prod["usine"].isin(usines) & df_prod["gamme"].isin(gammes)]

# ---------- KPIs ----------
st.subheader("Indicateurs cles")

total_pieces = len(df_p)
total_pannes = int(df_p["machine_failure"].sum())
taux_rebut = (total_pannes / total_pieces * 100) if total_pieces else 0
trs_moy = (df_k["trs"].mean() * 100) if len(df_k) else 0
energie = df_k["energie_kwh"].sum() if len(df_k) else 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("Pieces produites", f"{total_pieces:,}".replace(",", " "))
with c2:
    kpi_card("TRS moyen", f"{trs_moy:.1f}%", help_txt="Disponibilite x Performance x Qualite")
with c3:
    kpi_card("Taux rebut", f"{taux_rebut:.2f}%")
with c4:
    kpi_card("Pannes totales", f"{total_pannes}")
with c5:
    kpi_card("Energie", f"{energie:.0f} kWh")

st.divider()

# ---------- Graphes principaux ----------
colA, colB = st.columns(2)

with colA:
    st.subheader("TRS journalier par usine")
    if len(df_k):
        fig = px.line(
            df_k, x="jour", y="trs", color="usine", markers=True, line_shape="spline"
        )
        fig.update_layout(
            yaxis_tickformat=".0%",
            yaxis_title="TRS",
            xaxis_title="",
            height=380,
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.2),
        )
        fig.add_hline(
            y=0.85, line_dash="dash", line_color="green",
            annotation_text="Objectif 85%",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pas de donnees sur la periode.")

with colB:
    st.subheader("Taux de rebut journalier")
    if len(df_k):
        fig = px.bar(
            df_k, x="jour", y="taux_rebut_pct", color="usine", barmode="group"
        )
        fig.update_layout(
            yaxis_title="Rebut (%)",
            xaxis_title="",
            height=380,
            legend=dict(orientation="h", y=-0.2),
        )
        fig.add_hline(
            y=5, line_dash="dash", line_color="red", annotation_text="Seuil alerte 5%"
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------- Benchmark inter-usines ----------
st.subheader("Benchmark inter-usines")

bench = (
    df_k.groupby("usine")
    .agg(
        trs_moy=("trs", "mean"),
        rebut_pct=("taux_rebut_pct", "mean"),
        pieces=("pieces_produites", "sum"),
        energie_kwh=("energie_kwh", "sum"),
        dispo=("taux_dispo", "mean"),
    )
    .reset_index()
)
bench["trs_moy"] = (bench["trs_moy"] * 100).round(1)
bench["dispo"] = (bench["dispo"] * 100).round(1)
bench["rebut_pct"] = bench["rebut_pct"].round(2)

col1, col2 = st.columns([2, 3])
with col1:
    st.dataframe(
        bench.rename(
            columns={
                "usine": "Usine",
                "trs_moy": "TRS (%)",
                "rebut_pct": "Rebut (%)",
                "pieces": "Pieces",
                "energie_kwh": "Energie (kWh)",
                "dispo": "Dispo (%)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

with col2:
    if len(bench):
        cats = ["TRS", "Disponibilite", "Qualite", "Productivite"]
        fig = go.Figure()
        max_p = max(bench["pieces"].max(), 1)
        for _, row in bench.iterrows():
            fig.add_trace(
                go.Scatterpolar(
                    r=[
                        row["trs_moy"],
                        row["dispo"],
                        max(0, 100 - row["rebut_pct"] * 10),
                        row["pieces"] / max_p * 100,
                    ],
                    theta=cats,
                    fill="toself",
                    name=row["usine"],
                )
            )
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=340,
            showlegend=True,
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------- Causes de panne ----------
st.subheader("Typologie des defaillances (toutes usines)")
causes = pd.DataFrame(
    {
        "Cause": [
            "TWF (usure outil)",
            "HDF (chaleur)",
            "PWF (puissance)",
            "OSF (surcharge)",
            "RNF (aleatoire)",
        ],
        "Occurrences": [
            int(df_p["TWF"].sum()),
            int(df_p["HDF"].sum()),
            int(df_p["PWF"].sum()),
            int(df_p["OSF"].sum()),
            int(df_p["RNF"].sum()),
        ],
    }
)

if causes["Occurrences"].sum() > 0:
    fig = px.pie(causes, values="Occurrences", names="Cause", hole=0.5)
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune defaillance sur la periode filtree.")

st.divider()
st.caption(
    "Navigation : utiliser le menu lateral pour acceder aux vues Usine, IA Predictif, "
    "Alertes et Qualite des donnees."
)
