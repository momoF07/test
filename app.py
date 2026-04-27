import streamlit as st

# Charger le CSS personnalisé
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# Header en HTML pur
st.markdown("""
    <div class="main-header">
        <h1>Disney Tracker</h1>
        <p>Suivez vos aventures dans les parcs</p>
    </div>
    """, unsafe_allow_html=True)

# Utiliser les colonnes Streamlit pour la mise en page
col1, col2 = st.columns(2)

with col1:
    st.header("Parcs visités")
    # Ta logique Python ici
