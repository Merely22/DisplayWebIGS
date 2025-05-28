import streamlit as st
import pandas as pd
from datetime import datetime
import os 
from src.authenticator import SessionWithHeaderRedirection
from src.generate_files import download_file_zip
from src.maps import display_map
from src.generate_date import calculate_date
from src.nearest_station import find_nearest_station
from streamlit_option_menu import option_menu

st.set_page_config(layout="wide", page_title="GNSS NASA App")

# Sidebar with menu
with st.sidebar:
    selected = option_menu(
        menu_title="GNSS NASA App",
        options=["Station nearest", "Download files", "Visual Map"],
        icons=["rulers", "search", "map"],
        default_index=0
    )

# Load station data
data_path = "igs_stations.csv"
df = pd.read_csv(data_path, sep=";", header=0)

# =======================
# 1️⃣ Estaciones Cercanas
# =======================
if selected == "Station nearest":
    st.title("🔍 Estaciones más cercanas")
    lat = st.number_input("Ingrese latitud", format="%.6f")
    lon = st.number_input("Ingrese longitud", format="%.6f")
    if st.button("Find and display on map"):
        if df.empty:
            st.error("Station data not loaded.")
        else:
            estaciones_cercanas = find_nearest_station(data_path, lat, lon)
            st.success("Showing the 2 nearest stations on the map:")
            st.dataframe(estaciones_cercanas)
            mapa = display_map(data_path, user_coords=(lat, lon), nearest_stations=estaciones_cercanas["Site Name"].tolist())
            st.components.v1.html(mapa._repr_html_(), height=600)

# =======================
#  Descarga de Archivos
# =======================
elif selected == "Download files":
    st.title("📥 Descarga de Archivos GNSS")
    
    estacion = st.selectbox("Estación", df["Site Name"].unique())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        dia = st.number_input("Día", value=1, min_value=1, max_value=31, step=1)
    with col2:
        mes = st.number_input("Mes", value=5, min_value=1, max_value=12, step=1)
    with col3:
        anio = st.number_input("Año", value=2025, min_value=2023, step=1)

    if st.button("Descargar archivos"):
        try:
            fecha = datetime(anio, mes, dia)
            with st.spinner("🔄 Descargando archivos desde NASA..."):
                resultado, mensaje, zip_path = download_file_zip(fecha, estacion)
            if not resultado:
                st.warning(mensaje)
            else:
                st.success(mensaje)
                with open(zip_path, "rb") as f:
                    st.download_button("📦 Descargar archivo ZIP", f, file_name=os.path.basename(zip_path))
        except ValueError:
            st.error("Fecha inválida. Verifica el día, mes y año.")


# =======================
# Mapa Visual General
# =======================
elif selected == "Visual Map":
    st.title("🗺️ Mapa de Estaciones GNSS")
    mapa = display_map(data_path)
    st.components.v1.html(mapa._repr_html_(), height=600)
