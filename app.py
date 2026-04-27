import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
import pytz

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Disney Global Tracker 🏰",
    page_icon="🏰",
    layout="wide"
)

# --- CSS RADICAL (Anti-bugs de thèmes) ---
st.markdown("""
    <style>
    /* 1. On force le fond de TOUTE l'application en bleu */
    .stApp {
        background-color: #003399 !important;
    }

    /* 2. On force la Sidebar à rester BLANCHE avec du texte NOIR */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        background-color: #ffffff !important;
    }
    [data-testid="stSidebar"] * {
        color: #1f2937 !important;
    }
    /* Fix pour les Selectbox dans la sidebar */
    div[data-baseweb="select"] > div {
        background-color: #f3f4f6 !important;
        color: #1f2937 !important;
    }

    /* 3. Zone de contenu principal : Texte en BLANC */
    .stMainBlockContainer h1, .stMainBlockContainer h2, .stMainBlockContainer h3, 
    .stMainBlockContainer p, .stMainBlockContainer span, .stMainBlockContainer label {
        color: white !important;
    }

    /* 4. LES CARTES : On force tout pour éviter l'influence du Dark Mode */
    .ride-card {
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border-left: 10px solid;
        background-color: #ffffff !important; /* Fond blanc forcé */
        box-shadow: 4px 4px 10px rgba(0,0,0,0.3);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* On force le texte à l'intérieur des cartes en NOIR/GRIS FONCÉ */
    .ride-card .ride-name { 
        color: #111827 !important; 
        font-size: 1.1rem; 
        font-weight: bold; 
        margin: 0;
    }
    .ride-card .land-name { 
        color: #4b5563 !important; 
        font-size: 0.85rem;
    }
    .ride-card .wait-time { 
        color: #111827 !important; 
        font-size: 2.2rem; 
        font-weight: bold;
    }

    /* Bordures de statut */
    .status-open { border-left-color: #22c55e !important; }
    .status-incident { border-left-color: #f59e0b !important; }
    .status-closed { border-left-color: #ef4444 !important; }

    /* Correction des métriques */
    [data-testid="stMetricValue"] {
        color: white !important;
    }
    [data-testid="stMetricLabel"] {
        color: #e5e7eb !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE DE DONNÉES ---
@st.cache_data(ttl=60)
def fetch_data(p_id):
    try:
        r = requests.get(f"https://queue-times.com/parks/{p_id}/queue_times.json", timeout=10)
        return r.json()
    except: return None

def main():
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🌍 Destination")
        region = st.selectbox("Région", ["Disneyland Paris", "Walt Disney World (Florida)"])
        
        if region == "Disneyland Paris":
            p_map = {"Parc Disneyland": 4, "Walt Disney Studios": 28}
        else:
            p_map = {"Magic Kingdom": 6, "Epcot": 5, "Hollywood Studios": 7, "Animal Kingdom": 8}
            
        p_name = st.selectbox("Parc", list(p_map.keys()))
        p_id = p_map[p_name]
        
        if st.button("🔄 Actualiser"):
            st.cache_data.clear()
            st.rerun()

    # --- TITRE ---
    st.title(f"🏰 {p_name}")

    # --- DATA ---
    data = fetch_data(p_id)
    if data:
        # Extraction
        rows = []
        for l in data.get('lands', []):
            for r in l.get('rides', []):
                rows.append({"name": r['name'], "land": l['name'], "wait": r['wait_time'], "open": r['is_open']})
        df = pd.DataFrame(rows)
        
        # Stats
        open_df = df[df['open']]
        t_open = len(open_df)
        avg = int(open_df['wait'].mean()) if t_open > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Opérationnel", f"{t_open} / {len(df)}")
        c2.metric("Attente Moyenne", f"{avg} min")
        c3.metric("Statut", "OUVERT" if t_open > 0 else "FERMÉ")

        st.divider()

        # Grille
        df = df.sort_values(by=["open", "wait"], ascending=[False, False])
        cols = st.columns(2)
        
        for i, row in df.iterrows():
            if not row['open']:
                # Logique FIN vs 101 (Inspiration app (1).py)
                status, label, sub = ("status-closed", "FIN", "Fermé") if t_open == 0 else ("status-incident", "101", "Interruption")
            else:
                status, label, sub = "status-open", str(row['wait']), "Opérationnel"

            unit = "min" if label.isdigit() else ""

            with cols[i % 2]:
                st.markdown(f"""
                    <div class="ride-card {status}">
                        <div>
                            <p class="ride-name">{row['name']}</p>
                            <p class="land-name">{row['land']} • {sub}</p>
                        </div>
                        <div class="wait-time">
                            {label}<span style="font-size:0.8rem">{unit}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.error("L'API ne répond pas. Vérifie ta connexion.")

if __name__ == "__main__":
    main()
