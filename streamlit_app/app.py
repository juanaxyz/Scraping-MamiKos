"""
STREAMLIT: Worth-it Predictor
==============================
Prediksi apakah sebuah kos worth it berdasarkan karakteristiknya.
Model: Random Forest (trained on 358 kos di sekitar UNUD Jimbaran)
"""

import os, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, ConfusionMatrixDisplay

warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────
rpath = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(rpath, '..', 'data', 'processed', 'mamikos_clean.csv')

st.set_page_config(
    page_title='Worth-it Predictor',
    page_icon='🏠',
    layout='centered',
)

# ──────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────
def fr(v):
    if pd.isna(v) or v is None:
        return 'N/A'
    if v >= 1e6:
        return f'Rp {v/1e6:.2f}jt'
    if v >= 1e3:
        return f'Rp {v/1e3:.0f}rb'
    return f'Rp {v:.0f}'

def rupiah_input(v):
    return int(round(v / 100_000) * 100_000)

# ──────────────────────────────────────────────────────────
# [1] LOAD & PREPARE
# ──────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    dv = pd.read_csv(CSV)
    avg_pps = dv['pps'].mean()
    avg_dist = dv['jarak_unud_jimbaran_km'].mean()
    dv['fair_score'] = 100 - (
        abs(dv['pps'] - avg_pps) / avg_pps * 50 +
        abs(dv['jarak_unud_jimbaran_km'] - avg_dist) / avg_dist * 50
    ).clip(0, 100)
    median_fair = dv['fair_score'].median()
    dv['worth_it'] = (dv['fair_score'] >= median_fair).astype(int)
    return dv

dv = load_data()

# ──────────────────────────────────────────────────────────
# [2] TRAIN MODEL
# ──────────────────────────────────────────────────────────
@st.cache_resource
def train_model(data):
    data = data.dropna(subset=['price', 'size_area', 'jarak_unud_jimbaran_km', 'ft',
                                'pps', 'fac_room_AC', 'fac_share_WiFi',
                                'fac_bath_K. Mandi Dalam', 'gen', 'worth_it'])
    X = data[['price', 'size_area', 'jarak_unud_jimbaran_km', 'ft',
              'pps', 'fac_room_AC', 'fac_share_WiFi',
              'fac_bath_K. Mandi Dalam', 'gen']].copy()
    X['gen_encoded'] = (X['gen'] == 'Putri').astype(int)
    X.drop(columns=['gen'], inplace=True)
    y = data['worth_it']

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    y_pred = model.predict(X)
    metrics = {
        'accuracy': accuracy_score(y, y_pred),
        'precision': precision_score(y, y_pred),
        'recall': recall_score(y, y_pred),
        'f1': f1_score(y, y_pred),
    }
    cm = confusion_matrix(y, y_pred)
    feat_imp = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)

    return model, metrics, cm, feat_imp, X.columns.tolist()

model, metrics, cm, feat_imp, feat_cols = train_model(dv)

# ──────────────────────────────────────────────────────────
# [3] SIDEBAR — INPUT FORM
# ──────────────────────────────────────────────────────────
st.sidebar.title('🏠 Cek Kos Worth-it')
st.sidebar.markdown('Masukkan kriteria kos yang ingin dicek:')

budget = st.sidebar.slider(
    'Harga Bulanan', 500_000, 10_000_000, 2_500_000, 100_000,
    format='Rp %d'
)

jarak = st.sidebar.slider(
    'Jarak dari UNUD Jimbaran (km)',
    0.0, 10.0, 3.0, 0.5
)

luas = st.sidebar.slider(
    'Luas Kamar (m²)',
    0, 50, 12, 1
)

st.sidebar.markdown('**Fasilitas:**')
ac = st.sidebar.checkbox('AC', value=True)
wifi = st.sidebar.checkbox('WiFi', value=True)
km_dalam = st.sidebar.checkbox('K. Mandi Dalam', value=True)

gender = st.sidebar.radio('Gender Kos', ['Campur', 'Putri'])

predict_btn = st.sidebar.button('🔮 Cek Prediksi', type='primary', use_container_width=True)

# ──────────────────────────────────────────────────────────
# [4] MAIN PANEL — OUTPUT
# ──────────────────────────────────────────────────────────
st.title('🏠 Worth-it Predictor')
st.markdown('Prediksi apakah sebuah kos **worth it** berdasarkan harga, jarak, luas, dan fasilitas.')
st.markdown(f'Model dilatih dari **{len(dv)} kos** di sekitar UNUD Jimbaran.')
st.divider()

if not predict_btn:
    st.info('👈 Atur kriteria kos di sidebar, lalu klik **Cek Prediksi**')

else:
    # ── Buat input vector ──
    input_data = pd.DataFrame([{
        'price': float(budget),
        'size_area': float(luas),
        'jarak_unud_jimbaran_km': float(jarak),
        'ft': float(sum([ac, wifi, km_dalam])),
        'pps': float(budget) / float(luas) if luas > 0 else 0,
        'fac_room_AC': float(ac),
        'fac_share_WiFi': float(wifi),
        'fac_bath_K. Mandi Dalam': float(km_dalam),
        'gen_encoded': 1.0 if gender == 'Putri' else 0.0,
    }])

    # ── Predict ──
    proba = model.predict_proba(input_data)[0][1]
    pred = model.predict(input_data)[0]
    worth_it = bool(pred)

    # ── Fair score ──
    avg_pps = dv['pps'].mean()
    avg_dist = dv['jarak_unud_jimbaran_km'].mean()
    pps_val = float(budget) / float(luas) if luas > 0 else 0
    fair_score_input = 100 - (
        abs(pps_val - avg_pps) / avg_pps * 50 +
        abs(float(jarak) - avg_dist) / avg_dist * 50
    )
    fair_score_input = max(0, min(100, fair_score_input))

    # ══════════════════════════════════════════════════════
    # BADGE + PROBABILITY
    # ══════════════════════════════════════════════════════
    col_badge, col_score = st.columns([1, 2])

    with col_badge:
        if worth_it:
            st.markdown(
                f'<div style="text-align:center; padding:20px; '
                f'background:#d4edda; border-radius:15px; '
                f'border:3px solid #28a745;">'
                f'<h1 style="color:#155724; margin:0;">✅</h1>'
                f'<h2 style="color:#155724; margin:5px 0;">WORTH IT!</h2>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="text-align:center; padding:20px; '
                f'background:#f8d7da; border-radius:15px; '
                f'border:3px solid #dc3545;">'
                f'<h1 style="color:#721c24; margin:0;">❌</h1>'
                f'<h2 style="color:#721c24; margin:5px 0;">NOT WORTH IT</h2>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_score:
        pct = proba * 100
        st.metric('Confidence', f'{pct:.0f}%', delta=None)
        st.progress(int(pct), text='Worth-it Probability')

    st.divider()

    # ══════════════════════════════════════════════════════
    # FAIRNESS SCORE GAUGE
    # ══════════════════════════════════════════════════════
    st.subheader('📊 Fairness Score')
    st.markdown(
        f'Skor 0–100: semakin tinggi = semakin **sebanding** harga dengan luas & jarak.'
    )

    fig_g, ax_g = plt.subplots(figsize=(8, 1.5))
    ax_g.set_xlim(0, 100)
    ax_g.set_ylim(0, 1)
    colors_g = plt.cm.RdYlGn(fair_score_input / 100)
    ax_g.barh(0, fair_score_input, height=0.6, color=colors_g, edgecolor='black')
    ax_g.barh(0, 100, height=0.6, color='lightgray', edgecolor='black', alpha=0.3, zorder=0)
    ax_g.set_yticks([])
    ax_g.set_xticks(range(0, 101, 20))
    ax_g.text(fair_score_input + 1, 0, f'{fair_score_input:.0f}/100',
              va='center', fontsize=12, fontweight='bold', color='black')
    ax_g.spines['top'].set_visible(False)
    ax_g.spines['right'].set_visible(False)
    ax_g.spines['left'].set_visible(False)
    st.pyplot(fig_g)
    plt.close()

    st.divider()

    # ══════════════════════════════════════════════════════
    # TOP 3 FAKTOR
    # ══════════════════════════════════════════════════════
    st.subheader('🔍 3 Faktor Paling Berpengaruh')
    top3 = feat_imp.head(3)
    nama_fitur = {
        'price': 'Harga',
        'size_area': 'Luas Kamar',
        'jarak_unud_jimbaran_km': 'Jarak dari UNUD',
        'ft': 'Jumlah Fasilitas',
        'pps': 'Harga per m²',
        'fac_room_AC': 'AC',
        'fac_share_WiFi': 'WiFi',
        'fac_bath_K. Mandi Dalam': 'KM Dalam',
        'gen_encoded': 'Gender',
    }
    for i, (feat, imp) in enumerate(top3.items(), 1):
        label = nama_fitur.get(feat, feat)
        st.markdown(f'**{i}. {label}**  —  {imp*100:.0f}%')
        st.progress(int(imp * 100))

    st.divider()

    # ══════════════════════════════════════════════════════
    # INPUT SUMMARY
    # ══════════════════════════════════════════════════════
    st.subheader('📋 Ringkasan Input')
    cols = st.columns(4)
    cols[0].metric('Harga', f'{fr(budget)}')
    cols[1].metric('Jarak', f'{jarak:.1f} km')
    cols[2].metric('Luas', f'{luas} m²')
    cols[3].metric('Gender', gender)

    cols2 = st.columns(3)
    cols2[0].metric('AC', '✅' if ac else '❌')
    cols2[1].metric('WiFi', '✅' if wifi else '❌')
    cols2[2].metric('KM Dalam', '✅' if km_dalam else '❌')

    st.divider()

    # ══════════════════════════════════════════════════════
    # MODEL EVALUATION (expander)
    # ══════════════════════════════════════════════════════
    with st.expander('📊 Detail Performa Model'):
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric('Accuracy', f'{metrics["accuracy"]:.2f}')
        col_m2.metric('Precision', f'{metrics["precision"]:.2f}')
        col_m3.metric('Recall', f'{metrics["recall"]:.2f}')
        col_m4.metric('F1-Score', f'{metrics["f1"]:.2f}')

        fig_cm, ax_cm = plt.subplots(figsize=(5, 4))
        ConfusionMatrixDisplay(cm, display_labels=['Not Worth', 'Worth']).plot(
            ax=ax_cm, cmap='Blues', values_format='d'
        )
        ax_cm.set_title('Confusion Matrix')
        st.pyplot(fig_cm)
        plt.close()

        st.markdown('**Feature Importance (semua fitur):**')
        fig_fi, ax_fi = plt.subplots(figsize=(8, 4))
        colors_fi = plt.cm.Blues(np.linspace(0.3, 0.9, len(feat_imp)))
        ax_fi.barh(
            [nama_fitur.get(f, f) for f in feat_imp.index],
            feat_imp.values, color=colors_fi, edgecolor='black'
        )
        ax_fi.set_xlabel('Importance')
        ax_fi.invert_yaxis()
        st.pyplot(fig_fi)
        plt.close()

        st.caption(
            f'Model: Random Forest (100 trees) | '
            f'Training data: {len(dv)} samples | '
            f'Target: worth_it = fair_score ≥ median({dv["fair_score"].median():.0f})'
        )

# ──────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────
st.divider()
st.caption(
    'Sumber data: Mamikos.com — kos di area Jimbaran, Badung & Denpasar. '
    'Model untuk tujuan edukasi, bukan keputusan finansial.'
)
