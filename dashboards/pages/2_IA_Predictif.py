"""
Page IA Predictif - test du modele ML en direct.
"""
import json
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="IA Predictif", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "data" / "gold" / "best_model.joblib"
INFO_PATH = PROJECT_ROOT / "data" / "gold" / "best_model_info.json"

st.title("Intelligence artificielle - Prediction de defaillance")

# ---------- Guards ----------
if not MODEL_PATH.exists() or not INFO_PATH.exists():
    st.error("Modele non trouve. Executer le notebook 07.")
    st.stop()

info = json.loads(INFO_PATH.read_text())
model = joblib.load(MODEL_PATH)
FEATURE_ORDER = info["features"]


# ---------- Comparaison des modeles ----------
st.subheader("Benchmark des modeles")
st.caption(
    f"Meilleur modele retenu : {info['best_model']} - "
    f"PR-AUC = {info['metrics']['pr_auc']:.3f} "
    f"(seuil grille MSPR : > 0.5)"
)

df_models = pd.DataFrame(info["all_results"]).T.reset_index().rename(
    columns={"index": "modele"}
)
df_models = df_models.round(3)

c1, c2 = st.columns([2, 3])
with c1:
    st.dataframe(df_models, use_container_width=True, hide_index=True)

with c2:
    melted = df_models.melt(id_vars="modele", var_name="metrique", value_name="valeur")
    fig = px.bar(melted, x="modele", y="valeur", color="metrique", barmode="group")
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------- Prediction interactive ----------
st.subheader("Tester le modele - prediction en direct")
st.caption(
    "Ajuster les parametres d'une piece en production pour calculer instantanement "
    "la probabilite de defaillance."
)

c1, c2, c3 = st.columns(3)

with c1:
    air_temp = st.slider("Air temp (K)", 295.0, 305.0, 300.0, 0.1)
    proc_temp = st.slider("Process temp (K)", 305.0, 315.0, 310.0, 0.1)

with c2:
    rpm = st.slider("Vitesse rotation (rpm)", 1100, 2900, 1500)
    torque = st.slider("Couple (Nm)", 0.0, 80.0, 40.0, 0.5)

with c3:
    wear = st.slider("Usure outil (min)", 0, 260, 100)
    type_ = st.selectbox("Gamme", ["L", "M", "H"])
    usine = st.selectbox("Usine", ["FR-01", "ES-01"])


def build_feature_row(air_temp, proc_temp, rpm, torque, wear, type_, usine):
    """Construit une ligne conforme au modele (memes colonnes et ordre)."""
    row = {
        "Air_temperature_K": air_temp,
        "Process_temperature_K": proc_temp,
        "Rotational_speed_rpm": rpm,
        "Torque_Nm": torque,
        "Tool_wear_min": wear,
    }

    omega = rpm * 2 * 3.14159265 / 60
    row["delta_temp"] = proc_temp - air_temp
    row["puissance_w"] = torque * omega
    row["ratio_torque_rpm"] = torque / rpm if rpm else 0
    row["torque_x_wear"] = torque * wear
    row["temp_x_rpm"] = proc_temp * rpm
    row["energy_per_piece_wh"] = torque * omega * 60 / 3600

    # OneHot Type
    for t in ["L", "M", "H"]:
        row[f"type_{t}"] = 1 if type_ == t else 0

    # OneHot usine
    for u in ["FR-01", "ES-01"]:
        row[f"usine_{u}"] = 1 if usine == u else 0

    # OneHot wear bin
    if wear < 50:
        wear_bin = "neuf"
    elif wear < 150:
        wear_bin = "use"
    else:
        wear_bin = "critique"
    for w in ["neuf", "use", "critique"]:
        row[f"wear_{w}"] = 1 if wear_bin == w else 0

    df = pd.DataFrame([row])

    # Alignement avec les colonnes du modele
    for col in FEATURE_ORDER:
        if col not in df.columns:
            df[col] = 0
    df = df[FEATURE_ORDER]
    return df


if st.button("Predire", type="primary", use_container_width=True):
    X = build_feature_row(air_temp, proc_temp, rpm, torque, wear, type_, usine)

    try:
        proba = float(model.predict_proba(X)[0, 1])
    except Exception as e:
        st.error(f"Erreur de prediction : {e}")
        st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        if proba > 0.5:
            st.error(f"Probabilite de defaillance : {proba:.1%}")
            st.markdown("Action recommandee : arret immediat et inspection.")
        elif proba > 0.2:
            st.warning(f"Probabilite de defaillance : {proba:.1%}")
            st.markdown("Action recommandee : maintenance planifiee.")
        else:
            st.success(f"Probabilite de defaillance : {proba:.1%}")
            st.markdown("Statut : production normale.")

    with col2:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=proba * 100,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Risque de defaillance (%)"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "steps": [
                        {"range": [0, 20], "color": "#dcfce7"},
                        {"range": [20, 50], "color": "#fef08a"},
                        {"range": [50, 100], "color": "#fecaca"},
                    ],
                    "bar": {"color": "#1e40af"},
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 30,
                    },
                },
            )
        )
        fig.update_layout(height=280, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------- Interpretation ----------
st.subheader("Interpretation")

st.markdown(
    f"""
**Modele deploye :** `{info['best_model']}`

**Metriques cles (test set) :**

- PR-AUC : {info['metrics']['pr_auc']:.3f}
- ROC-AUC : {info['metrics']['roc_auc']:.3f}
- F1 : {info['metrics']['f1']:.3f}
- Precision : {info['metrics']['precision']:.3f}
- Recall : {info['metrics']['recall']:.3f}

**Choix methodologiques :**

1. PR-AUC comme metrique principale : la classe "Panne" est rare (environ 3.4 %),
   la ROC-AUC surestimerait la performance. La Precision-Recall AUC est plus fiable
   sur les donnees desequilibrees.

2. Class weight balance (LogReg/RF) et scale_pos_weight (XGBoost) compensent
   automatiquement le desequilibre a l'entrainement.

3. Seuil operationnel fixe a 30 % : au-dessus de cette probabilite, une alerte
   `ml_risque_eleve` est levee (voir notebook 08). Le seuil doit etre calibre avec
   l'equipe qualite selon le cout d'un faux positif (arret inutile) vs faux negatif
   (panne non anticipee).

**Limites :**

- Modele entraine sur donnees synthetiques (AI4I). Un re-entrainement sur les vraies
  donnees MECHA sera necessaire en production.
- Pas de suivi du drift en temps reel - a implementer avec MLflow lors de l'itération
  suivante.
"""
)
