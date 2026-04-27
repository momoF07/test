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

# --- STYLE CSS (Inspiré de ton ancien UI) ---
st.markdown("""
    <style>
    .ride-card {
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border-left: 10px solid;
        background-color: white;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .status-open { border-left-color: #28a745; }      /* Vert */
    .status-incident { border-left-color: #f39c12; }  /* Orange (Panne/101) */
    .status-closed { border-left-color: #c0392b; }    /* Bordeaux (Fermé/FIN) */
    
    .wait-time { 
        font-size: 2rem; 
        font-weight: bold; 
        color: #2c3e50;
        text-align: right;
    }
    .ride-name { font-size: 1.1rem; font-weight: 600; margin: 0; }
    .land-name { font-size: 0.85rem; color: #7f8c8d; }
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
    st.markdown("""
    <style>
    /* Change le fond de la zone principale */
    .stApp {
        background-color: #f0f2f6; /* Remplace par ta couleur (ex: #003399 pour un bleu Disney) */
    }
    
    /* Change aussi le fond de la barre latérale si besoin */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🏰 Disney World-Wide Live Board")

    # --- BARRE LATÉRALE DE SÉLECTION ---
    with st.sidebar:
        st.header("🌍 Destination")
        
        region = st.selectbox("Choisir une région", list(TZ_MAP.keys()))
        
        # Configuration des parcs selon la région
        if region == "Disneyland Paris":
            parks_config = {"Disneyland Parc": 4, "Walt Disney Studios": 28}
        elif region == "Walt Disney World (Florida)":
            parks_config = {"Magic Kingdom": 6, "Epcot": 5, "Hollywood Studios": 7, "Animal Kingdom": 8}
        else: # California
            parks_config = {"Disneyland Park": 16, "CA Adventure": 17}

        park_name = st.selectbox("Choisir un parc", list(parks_config.keys()))
        park_id = parks_config[park_name]

        # Affichage de l'heure locale du parc
        local_tz = pytz.timezone(TZ_MAP[region])
        local_time = datetime.now(local_tz)
        st.metric(f"Heure à {region}", local_time.strftime("%H:%M"))
        
        st.divider()
        if st.button("🔄 Actualiser les temps"):
            st.cache_data.clear()
            st.rerun()

    # --- RÉCUPÉRATION DES DONNÉES ---
    with st.spinner(f"Connexion à {park_name}..."):
        data = fetch_park_data(park_id)

    if not data:
        st.error("❌ Erreur de connexion aux serveurs Disney. Réessayez dans quelques instants.")
        return

    # Transformation en DataFrame
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
        st.warning("Aucune donnée disponible pour ce parc actuellement.")
        return

    # --- METRICS DU DASHBOARD ---
    open_df = df[df['is_open']]
    total_rides = len(df)
    total_open = len(open_df)
    avg_wait = int(open_df['wait'].mean()) if total_open > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Opérationnel", f"{total_open} / {total_rides}")
    m2.metric("Attente Moyenne", f"{avg_wait} min")
    m3.metric("État du Parc", "OUVERT" if total_open > 0 else "FERMÉ", 
              delta=None if total_open > 0 else "Nuit / Maintenance", delta_color="inverse")

    st.divider()

    # --- AFFICHAGE DES CARDS (GRID) ---
    st.subheader(f"📍 {park_name} - Temps d'attente")
    
    # On trie pour mettre les favoris ou les plus longues attentes en premier
    df = df.sort_values(by=["is_open", "wait"], ascending=[False, False])
    
    cols = st.columns(2)
    for idx, (_, row) in enumerate(df.iterrows()):
        # Détermination du style (Logique de ton ancien code)
        if not row['is_open']:
            # On vérifie si c'est la nuit (toutes les attractions fermées) ou une panne isolée
            if total_open == 0:
                status_class = "status-closed"
                label = "FIN"
                sub_text = "Fermé pour la nuit"
            else:
                status_class = "status-incident"
                label = "101"
                sub_text = "Interruption temporaire"
        else:
            status_class = "status-open"
            label = str(row['wait'])
            sub_text = "✅ Opérationnel"

        unit = "min" if label.isdigit() else ""

        with cols[idx % 2]:
            st.markdown(f"""
                <div class="ride-card {status_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="max-width: 70%;">
                            <p class="ride-name">{row['name']}</p>
                            <span class="land-name">{row['land']} • {sub_text}</span>
                        </div>
                        <div class="wait-time">
                            {label}<span style="font-size:0.8rem; margin-left:2px;">{unit}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # --- ANALYSE ---
    if total_open > 0:
        st.divider()
        st.subheader("📊 Graphique des attentes")
        fig = px.bar(
            open_df.nlargest(15, 'wait'), 
            x='wait', 
            y='name', 
            orientation='h',
            color='wait',
            color_continuous_scale='Reds',
            labels={'wait': 'Minutes', 'name': ''}
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
