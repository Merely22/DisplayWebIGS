import streamlit as st
import pandas as pd
from nearest_station import find_nearest_station
from maps import display_map

# Set up
st.set_page_config(page_title="Metta - GNSS Data Collection", layout="wide", page_icon= "🛰️")

st.sidebar.title("Menú de herramientas")
opcion = st.sidebar.selectbox("Selecciona una herramienta:", [
    "INICIO",
    "International GNSS Service (IGS)",
    "NOAA National Geodetic Survey (NGS)"
])

# Load station data
data_path = "data/igs_stations.csv"
df = pd.read_csv(data_path, sep=",", header=0)
df.columns = df.columns.str.strip().str.lower()

if opcion == "INICIO":
    st.title("Find the nearest station ")
    data_path = "data/igs_stations.csv"
    df = pd.read_csv(data_path, sep=",", header=0)
    df.columns = df.columns.str.strip().str.lower()


    lat = st.number_input("Ingrese latitud", format="%.6f")
    lon = st.number_input("Ingrese longitud", format="%.6f")
    if st.button("Find and display on map"):
        if df.empty:
            st.error("Station data not loaded.")
        else:
            estaciones_cercanas = find_nearest_station(data_path, lat, lon)
            st.success("Showing the 2 nearest stations on the map:")
            st.dataframe(estaciones_cercanas)
            mapa = display_map_dual(data_path, user_coords=(lat, lon), 
                               nearest_stations=estaciones_cercanas["site name"].tolist())
            st.components.v1.html(mapa._repr_html_(), height=600)

    st.title("🗺️ Mapa de Estaciones GNSS")
    mapa = display_map(data_path)
    st.components.v1.html(mapa._repr_html_(), height=600)


elif opcion == "International GNSS Service (IGS)":
    from IGS import app as igs_app
    igs_app.main() 

elif opcion == "NOAA National Geodetic Survey (NGS)":
    from NGS import app as ngs_app
    ngs_app.main()
