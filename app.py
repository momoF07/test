import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, time
import pytz

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Disney Live Board Pro",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONSTANTES & CONFIG ---
PARIS_TZ = pytz.timezone('Europe/Paris')
DLP_CLOSING = time(22, 0)
DAW_CLOSING = time(21, 0)

# --- STYLE CSS (Inspiration de ton ancien apply_custom_style) ---
st.markdown("""
    <style>
    .ride-card {
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border-left: 8px solid;
    }
    .status-open { border-left-color: #28a745; background-color: #f8fff9; }
    .status-closed { border-left-color: #dc3545; background-color: #fff8f8; }
    .status-incident { border-left-color: #ffc107; background-color: #fffdf5; }
    .wait-time { font-size: 2rem; font-weight: bold; color: #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DE DONNÉES ---
@st.cache_data(ttl=60)
def fetch_disney_data(park_id):
    url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
    try:
        res = requests.get(url)
        return res.json()
    except:
        return None

def get_status_logic(ride, current_time):
    """Logique de statut inspirée de ton ancien code"""
    is_open = ride['is_open']
    wait = ride['wait_time']
    
    # Simulation de la logique de fermeture selon le parc (Studios vs Parc)
    # Dans une version complète, on mapperait chaque ride à son parc
    limit_h = DLP_CLOSING 
    
    if current_time >= limit_h:
        return "FERMÉ", "card-closed", "🏁 Fermé"
    elif not is_open:
        return "PANNE", "status-incident", "⚠️ Interruption"
    else:
        return f"{wait} min", "status-open", "✅ Opérationnel"

# --- INTERFACE PRINCIPALE ---
def main():
    now = datetime.now(PARIS_TZ).time()
    
    st.title("🏰 Disney Live Board")
    
    # Barre latérale : Gestion des Favoris (via Query Params comme dans ton code)
    if "fav" not in st.query_params:
        st.query_params["fav"] = []
    
    with st.sidebar:
        st.header("📍 Sélection")
        destination = st.radio("Destination", ["Disneyland Parc", "Walt Disney Studios"])
        park_id = 4 if destination == "Disneyland Parc" else 28
        
        st.divider()
        if st.button("🔄 Forcer la mise à jour"):
            st.cache_data.clear()
            st.rerun()

    # Récupération des données
    data = fetch_disney_data(park_id)
    
    if data:
        all_rides = []
        for land in data['lands']:
            for ride in land['rides']:
                ride['land_name'] = land['name']
                all_rides.append(ride)
        
        df = pd.DataFrame(all_rides)

        # --- FILTRES RAPIDES ---
        fav_list = st.multiselect(
            "⭐ Vos attractions favorites", 
            options=df['name'].unique(),
            default=[f for f in st.query_params.get_all("fav") if f in df['name'].values]
        )
        st.query_params["fav"] = fav_list

        # --- AFFICHAGE ---
        display_list = df[df['name'].isin(fav_list)] if fav_list else df

        # Stats rapides
        c1, c2, c3 = st.columns(3)
        c1.metric("Ouvertes", len(df[df['is_open']]))
        c2.metric("En Panne", len(df[~df['is_open']]))
        c3.metric("Attente Moyenne", f"{int(df[df['is_open']]['wait_time'].mean())} min")

        st.divider()

        # Grille d'affichage
        cols = st.columns(2)
        for idx, row in display_list.iterrows():
            with cols[idx % 2]:
                label, style_class, sub_text = get_status_logic(row, now)
                
                st.markdown(f"""
                    <div class="ride-card {style_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h3 style="margin:0;">{row['name']}</h3>
                                <small>{row['land_name']} • {sub_text}</small>
                            </div>
                            <div class="wait-time">{label}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # --- ANALYSE GRAPHIQUE ---
        if not fav_list:
            st.subheader("📈 Top 10 des attentes")
            top_df = df[df['is_open']].nlargest(10, 'wait_time')
            fig = px.bar(top_df, x='wait_time', y='name', orientation='h', 
                         color='wait_time', color_continuous_scale='RdYlGn_r')
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("Impossible de joindre les serveurs Disney.")

if __name__ == "__main__":
    main()
