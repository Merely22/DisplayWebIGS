import streamlit as st
import pandas as pd
from maps import display_map
from PIL import Image

# Set up page
st.set_page_config(
    page_title="Metta - GNSS Data Collection",
    layout="wide",
    page_icon="🛰️"
)

# Title
st.title("🌍 GNSS Data Collection")

# Sidebar title and logo
st.sidebar.image("files/metta_logo_hd.png", use_container_width=True)
st.sidebar.title("Tools Menu")
opcion = st.sidebar.selectbox("Select a tool:", [
    "Home",
    "International GNSS Service (IGS)",
    "NOAA National Geodetic Survey (NGS)",
    "European Reference Frame (EUREF)",
    "Precise Orbits Download"
])

if opcion == "Home":
    # Define rutas a los CSVs locales
    path_igs = "data/igs_stations.csv"
    path_noaa = "data/noaa_cors.csv"
    path_euref = "data/EUREF_High-Rate.csv"

    # Llama a la función de visualización completa
    display_map(path_igs, path_noaa, path_euref)

elif opcion == "International GNSS Service (IGS)":
    from IGS import app as igs_app
    igs_app.main()

elif opcion == "NOAA National Geodetic Survey (NGS)":
    from NGS import app as ngs_app
    ngs_app.main()

elif opcion == "European Reference Frame (EUREF)":
    from EUREF import app as euref_app
    euref_app.main()

elif opcion == "Precise Orbits Download":
    from efemerides import app as efemerides_app
    efemerides_app.main()
