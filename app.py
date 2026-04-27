import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Disney Live Tracker",
    page_icon="🎢",
    layout="wide"
)

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .closed-status { color: #ff4b4b; font-weight: bold; }
    .open-status { color: #28a745; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE DE RÉCUPÉRATION DES DONNÉES ---
@st.cache_data(ttl=60)  # Mise à jour toutes les 60 secondes
def fetch_park_data(park_id):
    url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

def process_data(data):
    all_rides = []
    for land in data.get('lands', []):
        for ride in land.get('rides', []):
            all_rides.append({
                "Zone": land['name'],
                "Attraction": ride['name'],
                "Attente": ride['wait_time'],
                "Statut": "Ouvert" if ride['is_open'] else "Interrompu",
                "Dernière mise à jour": datetime.now().strftime("%H:%M")
            })
    return pd.DataFrame(all_rides)

# --- INTERFACE UTILISATEUR ---
def main():
    st.title("🏰 Disney World-Wide Tracker")
    st.markdown("Suivez les temps d'attente et l'état des attractions en temps réel.")

    # Barre latérale : Sélection du parc
    with st.sidebar:
        st.header("Paramètres")
        destination = st.selectbox("Destination", ["Disneyland Paris", "Walt Disney World (Florida)", "Disneyland Resort (California)"])
        
        # Mapping des IDs de l'API
        parks_map = {
            "Disneyland Paris": {"Parc Disneyland": 4, "Walt Disney Studios": 28},
            "Walt Disney World (Florida)": {"Magic Kingdom": 6, "Epcot": 5, "Hollywood Studios": 7, "Animal Kingdom": 8},
            "Disneyland Resort (California)": {"Disneyland Park": 16, "California Adventure": 17}
        }
        
        selected_park_name = st.selectbox("Parc spécifique", list(parks_map[destination].keys()))
        park_id = parks_map[destination][selected_park_name]
        
        if st.button("🔄 Actualiser les données"):
            st.cache_data.clear()

    # Récupération des données
    with st.spinner('Récupération de la magie en cours...'):
        raw_data = fetch_park_data(park_id)

    if raw_data:
        df = process_data(raw_data)
        
        # --- RÉSUMÉ (METRICS) ---
        total_open = len(df[df['Statut'] == "Ouvert"])
        total_closed = len(df[df['Statut'] == "Interrompu"])
        avg_wait = int(df[df['Statut'] == "Ouvert"]['Attente'].mean())

        m1, m2, m3 = st.columns(3)
        m1.metric("Attractions Ouvertes", f"{total_open}/{len(df)}")
        m2.metric("Temps d'attente moyen", f"{avg_wait} min")
        m3.metric("Interruptions", total_closed, delta_color="inverse")

        # --- ALERTES INTERRUPTIONS ---
        if total_closed > 0:
            with st.expander("⚠️ Liste des attractions actuellement interrompues"):
                closed_list = df[df['Statut'] == "Interrompu"]['Attraction'].tolist()
                for ride in closed_list:
                    st.write(f"❌ {ride}")

        # --- VISUALISATION ---
        st.divider()
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("📊 Top 10 des temps d'attente")
            # Graphique des temps d'attente
            top_10 = df[df['Statut'] == "Ouvert"].nlargest(10, 'Attente')
            fig = px.bar(top_10, x='Attente', y='Attraction', orientation='h', 
                         color='Attente', color_continuous_scale='Reds',
                         labels={'Attente': 'Minutes', 'Attraction': ''})
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("📋 Liste complète")
            # Filtre par zone
            selected_land = st.multiselect("Filtrer par zone", df['Zone'].unique())
            display_df = df if not selected_land else df[df['Zone'].isin(selected_land)]
            
            # Affichage du tableau
            st.dataframe(
                display_df[['Attraction', 'Attente', 'Statut']],
                hide_index=True,
                use_container_width=True
            )

    else:
        st.error("Impossible de récupérer les données. Vérifiez votre connexion ou réessayez plus tard.")

    # --- FOOTER ---
    st.divider()
    st.caption(f"Données fournies par Queue-Times.com • Dernière synchro : {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
