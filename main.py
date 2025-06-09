import streamlit as st
import pandas as pd
from maps import display_map
from PIL import Image
# Set up
st.set_page_config(page_title="Metta - GNSS Data Collection", layout="wide", page_icon= "🛰️")

st.sidebar.title("Menú de herramientas")
imagen_izq = Image.open("files/metta_logo_hd.png") 
st.logo(imagen_izq)

opcion = st.sidebar.selectbox("Selecciona una herramienta:", [
    "INICIO",
    "International GNSS Service (IGS)",
    "NOAA National Geodetic Survey (NGS)"
])

if opcion == "INICIO":
    # Define rutas a los CSVs locales
    path_igs = "data/igs_stations.csv"
    path_noaa = "data/noaa_cors.csv"

    # Llama a la función de visualización completa
    display_map(path_igs, path_noaa)

elif opcion == "International GNSS Service (IGS)":
    from IGS import app as igs_app
    igs_app.main() 

elif opcion == "NOAA National Geodetic Survey (NGS)":
    from NGS import app as ngs_app
    ngs_app.main()
