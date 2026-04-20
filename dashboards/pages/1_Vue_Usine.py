"""
Page Vue Usine - detail par site avec alertes recentes.
"""
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Vue Usine", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "gold" / "mecha.duckdb"
KPIS_JOUR_PATH = PROJECT_ROOT / "data" / "gold" / "kpis_jour.parquet"
KPIS_HEURE_PATH = PROJECT_ROOT / "data" / "gold" / "kpis_heure.parquet"
ALERTS_PATH = PROJECT_ROOT / "data" / "gold" / "alerts.parquet"


@st.cache_data(ttl=60)
def load_data(usine: str):
    con = duckdb.connect(str(DB_PATH), read_only=True)
    prod = con.execute(
        f"SELECT * FROM v_production WHERE usine = '{usine}' ORDER BY timestamp"
    ).df()
    con.close()

    kpis_j = pd.read_parquet(KPIS_JOUR_PATH)
    kpis_j = kpis_j[kpis_j["usine"] == usine].copy()
    kpis_j["jour"] = pd.to_datetime(kpis_j["jour"])

    kpis_h = pd.read_parquet(KPIS_HEURE_PATH)
    kpis_h = kpis_h[kpis_h["usine"] == usine].copy()
    kpis_h["heure"] = pd.to_datetime(kpis_h["heure"])

    return prod, kpis_j, kpis_h


@st.cache_data(ttl=60)
def load_alerts(usine: str) -> pd.DataFrame:
    if not ALERTS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_parquet(ALERTS_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df[df["usine"] == usine]


# ---------- Guards ----------
if not DB_PATH.exists():
    st.error("Entrepot non trouve. Executer les notebooks 02 a 05.")
    st.stop()

# ---------- Header ----------
st.title("Vue detaillee - Usine")

con = duckdb.connect(str(DB_PATH), read_only=True)
usines = sorted([r[0] for r in con.execute("SELECT DISTINCT usine FROM dim_usine").fetchall()])
con.close()

usine = st.sidebar.selectbox("Site", usines)

prod, kpis_j, kpis_h = load_data(usine)
df_alerts = load_alerts(usine)

# ---------- KPIs header ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pieces produites", f"{len(prod):,}".replace(",", " "))
c2.metric("TRS moyen", f"{kpis_j['trs'].mean()*100:.1f}%")
c3.metric("Taux rebut", f"{prod['machine_failure'].mean()*100:.2f}%")
c4.metric("Energie totale", f"{kpis_j['energie_kwh'].sum():.0f} kWh")

st.divider()

# ---------- Alertes actives ----------
st.subheader("Alertes recentes")

if len(df_alerts):
    cutoff = df_alerts["timestamp"].max() - pd.Timedelta(hours=48)
    recent = df_alerts[df_alerts["timestamp"] >= cutoff]

    for prio in ["critique", "majeur", "mineur"]:
        sub = recent[recent["priorite"] == prio]
        if len(sub):
            with st.expander(
                f"{len(sub)} alertes {prio} (48 dernieres heures)",
                expanded=(prio == "critique"),
            ):
                st.dataframe(
                    sub.sort_values("timestamp", ascending=False)[
                        ["timestamp", "code", "message", "valeur", "seuil"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
else:
    st.success("Aucune alerte active sur cette usine.")

st.divider()

# ---------- Suivi horaire ----------
st.subheader("Suivi horaire")

tab1, tab2, tab3 = st.tabs(["Production", "Qualite", "Machine"])

with tab1:
    fig = px.line(kpis_h, x="heure", y="pieces", markers=True)
    fig.update_layout(height=350, yaxis_title="Pieces / heure", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = px.line(kpis_h, x="heure", y="taux_rebut_pct", markers=True)
    fig.add_hline(y=5, line_dash="dash", line_color="red", annotation_text="Seuil 5%")
    fig.update_layout(height=350, yaxis_title="Rebut (%)", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=kpis_h["heure"], y=kpis_h["torque_moyen"], name="Moyenne"))
        fig.update_layout(height=320, title="Couple moyen (Nm)", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(kpis_h, x="heure", y="tool_wear_max")
        fig.add_hline(y=200, line_dash="dash", line_color="orange", annotation_text="Seuil 200 min")
        fig.update_layout(height=320, title="Usure outil max (min)", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------- Repartition gamme ----------
st.subheader("Repartition par gamme de piece")

gamme_stats = (
    prod.groupby("gamme")
    .agg(pieces=("piece_id", "count"), rebuts=("machine_failure", "sum"))
    .reset_index()
)
gamme_stats["rebut_pct"] = (gamme_stats["rebuts"] / gamme_stats["pieces"] * 100).round(2)

c1, c2 = st.columns(2)
with c1:
    fig = px.pie(gamme_stats, values="pieces", names="gamme", hole=0.4, title="Volume")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    fig = px.bar(
        gamme_stats, x="gamme", y="rebut_pct", color="gamme",
        title="Taux de rebut par gamme (%)"
    )
    st.plotly_chart(fig, use_container_width=True)
