import streamlit as st
import pandas as pd
from datetime import datetime
import os 
from src.authenticator import SessionWithHeaderRedirection
from src.generate_files import download_file_zip
from src.maps import display_map
from src.components import mostrar_info_estacion_resumida
from src.nearest_station import find_nearest_station
from streamlit_option_menu import option_menu
from src.sumary_checker import descargar_summary, parsear_summary, verificar_disponibilidad_summary, obtener_formato_rinex

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
df = pd.read_csv(data_path, sep=",", header=0)

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
    try:
        fecha = datetime(anio, mes, dia)
        anio_consulta = fecha.year
        df_summary_raw = descargar_summary(anio_consulta)
        df_summary = parsear_summary(df_summary_raw)
        mostrar_info_estacion_resumida(estacion, df_summary, df)

        # Validar disponibilidad
        disponible, mensaje_dispo = verificar_disponibilidad_summary(estacion, fecha, df_summary, df)
        st.markdown(f"**📝 Validación Summary:** {mensaje_dispo}")
        rinex_version = obtener_formato_rinex(estacion, df_summary)
        st.session_state["rinex_version"] = rinex_version if disponible else None
    except Exception as e:
            st.warning(f"No se pudo verificar disponibilidad: {e}")
    col4, col5 = st.columns(2)
    with col4:
        hora_inicio=st.number_input("Hora inicial (UTC): ", value=0, min_value=0, max_value=23, step=1)
    with col5:
        hora_fin=st.number_input("Hora final (UTC): ", value=24, min_value=0, max_value=24, step=1)


    if st.button("Descargar archivos"):
        if hora_fin<=hora_inicio:
            st.warning("Su hora final debe ser mayor que su hora inicial")
        try:
            fecha = datetime(anio, mes, dia)
            with st.spinner("🔄 Descargando archivos desde NASA..."):
                resultado, mensaje, zip_path, temp_dir = download_file_zip(fecha, estacion, hora_inicio, hora_fin)
            if not resultado:
                st.warning(mensaje)
            else:
                st.success(mensaje)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        "📦 Descargar archivo ZIP",
                        f,
                        file_name=os.path.basename(zip_path),
                        mime="application/zip"
                    )
                # Eliminar archivos temporales después de mostrar el botón
                temp_dir.cleanup()
        except ValueError:
            st.error("Fecha inválida. Verifica el día, mes y año.")



# =======================
# Mapa Visual General
# =======================
elif selected == "Visual Map":
    st.title("🗺️ Mapa de Estaciones GNSS")
    mapa = display_map(data_path)
    st.components.v1.html(mapa._repr_html_(), height=600)
