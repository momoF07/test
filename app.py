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

# --- STYLE CSS ---
st.markdown("""
    <style>
    .ride-card {
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border-left: 8px solid;
        background-color: white;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .status-open { border-left-color: #28a745; }
    .status-closed { border-left-color: #dc3545; }
    .status-incident { border-left-color: #ffc107; }
    .wait-time { font-size: 1.8rem; font-weight: bold; color: #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DE DONNÉES ---
@st.cache_data(ttl=60)
def fetch_disney_data(park_id):
    url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return None

def get_status_logic(ride, current_time):
    is_open = ride.get('is_open', False)
    wait = ride.get('wait_time', 0)
    
    # Heure de fermeture théorique (simplifiée)
    limit_h = DLP_CLOSING 
    
    if current_time >= limit_h:
        return "FIN", "status-closed", "🏁 Fermé"
    elif not is_open:
        return "101", "status-incident", "⚠️ Interruption"
    else:
        return f"{wait}", "status-open", "✅ Opérationnel"

# --- INTERFACE PRINCIPALE ---
def main():
    now = datetime.now(PARIS_TZ).time()
    
    st.title("🏰 Disney Live Board")
    
    # Sidebar
    with st.sidebar:
        st.header("📍 Sélection")
        destination = st.radio("Destination", ["Disneyland Parc", "Walt Disney Studios"])
        park_id = 4 if destination == "Disneyland Parc" else 28
        
        st.divider()
        if st.button("🔄 Actualiser"):
            st.cache_data.clear()
            st.rerun()

    # Récupération des données
    data = fetch_disney_data(park_id)
    
    if data:
        all_rides = []
        for land in data.get('lands', []):
            for ride in land.get('rides', []):
                ride['land_name'] = land['name']
                all_rides.append(ride)
        
        df = pd.DataFrame(all_rides)

        if df.empty:
            st.warning("Aucune donnée disponible pour ce parc.")
            return

        # Gestion des favoris
        fav_list = st.multiselect(
            "⭐ Vos attractions favorites", 
            options=sorted(df['name'].unique()),
            default=[f for f in st.query_params.get_all("fav") if f in df['name'].values]
        )
        st.query_params["fav"] = fav_list

        # --- CALCULS SÉCURISÉS DES METRICS ---
        open_rides = df[df['is_open'] == True]
        total_open = len(open_rides)
        total_closed = len(df[df['is_open'] == False])
        
        # Correction du bug ValueError
        if total_open > 0:
            avg_wait = int(open_rides['wait_time'].mean())
        else:
            avg_wait = 0

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Ouvertes", f"{total_open}/{len(df)}")
        m2.metric("En Panne", total_closed)
        m3.metric("Attente Moyenne", f"{avg_wait} min")

        # --- AFFICHAGE DES CARDS ---
        display_df = df[df['name'].isin(fav_list)] if fav_list else df
        
        st.write("### Attractions")
        cols = st.columns(2)
        for idx, (_, row) in enumerate(display_df.iterrows()):
            with cols[idx % 2]:
                label, style_class, sub_text = get_status_logic(row, now)
                unit = "min" if label.isdigit() else ""
                
                st.markdown(f"""
                    <div class="ride-card {style_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin:0;">{row['name']}</h4>
                                <small style="color: #666;">{row['land_name']} • {sub_text}</small>
                            </div>
                            <div class="wait-time">{label}<span style="font-size:0.8rem">{unit}</span></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # --- GRAPHIQUE ---
        if total_open > 0:
            st.write("---")
            st.subheader("📈 Top 10 des attentes")
            top_df = open_rides.nlargest(10, 'wait_time')
            fig = px.bar(top_df, x='wait_time', y='name', orientation='h', 
                         color='wait_time', color_continuous_scale='Reds',
                         labels={'wait_time': 'Minutes', 'name': ''})
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("❌ Erreur de récupération des données Queue-Times.")

if __name__ == "__main__":
    main()
