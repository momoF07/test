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

# --- DICTIONNAIRE DES FUSEAUX HORAIRES ---
TZ_MAP = {
    "Disneyland Paris": "Europe/Paris",
    "Walt Disney World (Florida)": "US/Eastern",
    "Disneyland Resort (California)": "US/Pacific"
}

# --- STYLE CSS AVANCÉ (Anti-bugs) ---
st.markdown("""
    <style>
    /* 1. Fond principal bleu uniquement pour le contenu */
    .stMainBlockContainer {
        background-color: #003399 !important;
        color: white !important;
    }
    
    /* 2. Fix pour les titres et textes de la zone principale */
    .stMainBlockContainer h1, .stMainBlockContainer h2, .stMainBlockContainer h3, .stMainBlockContainer p, .stMainBlockContainer span {
        color: white !important;
    }

    /* 3. Protection de la Sidebar (fond blanc, texte noir) */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #31333F !important;
    }

    /* 4. Style des Cartes (Forcer le texte sombre pour la lisibilité sur fond blanc) */
    .ride-card {
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border-left: 10px solid;
        background-color: white !important;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
    }
    .ride-card p, .ride-card span, .ride-card div {
        color: #2c3e50 !important;
    }
    
    .status-open { border-left-color: #28a745 !important; }
    .status-incident { border-left-color: #f39c12 !important; }
    .status-closed { border-left-color: #c0392b !important; }
    
    .wait-time { 
        font-size: 2rem; 
        font-weight: bold; 
        text-align: right;
    }
    .ride-name { font-size: 1.1rem; font-weight: 600; margin: 0; }
    .land-name { font-size: 0.85rem; color: #7f8c8d !important; }

    /* 5. Fix pour les Dividers qui disparaissent sur le bleu */
    hr { border-color: rgba(255, 255, 255, 0.3) !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_park_data(park_id):
    url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except:
        return None

def main():
    st.title("🏰 Disney World-Wide Live Board")

    # --- BARRE LATÉRALE ---
    with st.sidebar:
        st.header("🌍 Destination")
        region = st.selectbox("Choisir une région", list(TZ_MAP.keys()))
        
        if region == "Disneyland Paris":
            parks_config = {"Disneyland Parc": 4, "Walt Disney Studios": 28}
        elif region == "Walt Disney World (Florida)":
            parks_config = {"Magic Kingdom": 6, "Epcot": 5, "Hollywood Studios": 7, "Animal Kingdom": 8}
        else:
            parks_config = {"Disneyland Park": 16, "CA Adventure": 17}

        park_name = st.selectbox("Choisir un parc", list(parks_config.keys()))
        park_id = parks_config[park_name]

        local_tz = pytz.timezone(TZ_MAP[region])
        local_time = datetime.now(local_tz)
        st.metric(f"Heure locale", local_time.strftime("%H:%M"))
        
        st.divider()
        if st.button("🔄 Actualiser les temps", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # --- RÉCUPÉRATION DATA ---
    with st.spinner(f"Connexion à {park_name}..."):
        data = fetch_park_data(park_id)

    if not data:
        st.error("❌ Impossible de charger les données.")
        return

    all_rides = []
    for land in data.get('lands', []):
        for ride in land.get('rides', []):
            all_rides.append({
                "name": ride['name'],
                "land": land['name'],
                "wait": ride['wait_time'],
                "is_open": ride['is_open']
            })
    
    df = pd.DataFrame(all_rides)
    if df.empty:
        st.warning("Aucune donnée disponible.")
        return

    # --- METRICS ---
    open_df = df[df['is_open']]
    total_open = len(open_df)
    avg_wait = int(open_df['wait'].mean()) if total_open > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Opérationnel", f"{total_open} / {len(df)}")
    m2.metric("Attente Moyenne", f"{avg_wait} min")
    m3.metric("État du Parc", "OUVERT" if total_open > 0 else "FERMÉ")

    st.divider()

    # --- AFFICHAGE GRID ---
    st.subheader(f"📍 {park_name}")
    df = df.sort_values(by=["is_open", "wait"], ascending=[False, False])
    
    cols = st.columns(2)
    for idx, (_, row) in enumerate(df.iterrows()):
        if not row['is_open']:
            if total_open == 0:
                status_class, label, sub = "status-closed", "FIN", "Fermé"
            else:
                status_class, label, sub = "status-incident", "101", "Interruption"
        else:
            status_class, label, sub = "status-open", str(row['wait']), "Opérationnel"

        unit = "min" if label.isdigit() else ""

        with cols[idx % 2]:
            st.markdown(f"""
                <div class="ride-card {status_class}">
                    <div style="max-width: 75%;">
                        <p class="ride-name">{row['name']}</p>
                        <span class="land-name">{row['land']} • {sub}</span>
                    </div>
                    <div class="wait-time">
                        {label}<span style="font-size:0.8rem; margin-left:2px;">{unit}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
