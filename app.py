import streamlit as st
import pandas as pd
from datetime import date
from src.authenticator import SessionWithHeaderRedirection
from src.generate_files import download_file_zip
from src.maps import display_map
from src.generate_date import calculate_date
from src.nearest_station import find_nearest_station
from streamlit_option_menu import option_menu

#=================================================================
# Título
st.set_page_config(page_title="GNSS Downloader", layout="centered")
st.title("GNSS Downloader IGS - CDDS")
#=================================================================
# Subida del CSV (o carga directa)
ruta_csv = "igs_stations.csv"
df = pd.read_csv(ruta_csv, sep=";",header=0)

# Sidebar

with st.sidebar:
    selected = option_menu(
    menu_title="Overview",
    options=["Station nearest","Download files", "Visual Map" ],
    icons=[ "rulers","search","map"],
    default_index=0
    )

#==============================================================  
                  
if selected == "Station nearest":
    st.subheader("Find and Show Nearest IGS Stations")

    lat = st.number_input("Enter latitude", format="%.6f")
    lon = st.number_input("Enter longitude", format="%.6f")

    if st.button("Find and display on map"):
        if df.empty:
            st.error("Station data not loaded.")
        else:
            nearest_stations = find_nearest_station(lat, lon, df)

            st.success("Showing the 2 nearest stations on the map:")
            st.dataframe(nearest_stations[["Site Name", "Latitude", "Longitude", "Distance_km"]])

            # Call map function
            find_nearest_station(lat, lon, nearest_stations)

elif selected == "Download files":
    st.subheader("Select Station")

    estacion = st.selectbox("Estación", df["Site Name"])
    col1, col2, col3 = st.columns(3)
    with col1:
        dia = st.number_input("Día", value=1, min_value=1, max_value=31, step=1)
    with col2:
        mes = st.number_input("Mes", value=5, min_value=1, max_value=12, step=1)
    with col3:
        anio = st.number_input("Año", value=2025, step=1, min_value= 2024)


    if st.button("Descargar archivos"):

        with st.spinner("Espere unos minutos ..."):
            session = SessionWithHeaderRedirection()
            session.headers.update({"User-Agent": "Mozilla/5.0"})

            try:
                zip_buffer, nombre_zip = download_file_zip(anio, mes, dia, estacion, session, guardar_zip_local=True)

                st.success("¡Descarga lista!")

                st.download_button(
                    label="Descargar ZIP",
                    data=zip_buffer,
                    file_name=nombre_zip,
                    mime="application/zip"
                )
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")

elif selected == "Visual Map":
    st.subheader("Sation Maps IGS")
    display_map(ruta_csv)


