import streamlit as st
import pandas as pd
from src.authenticator import SessionWithHeaderRedirection
from src.generate_files import download_file_zip
from src.maps import display_map
from src.generate_date import calculate_date

# Título
st.title("GNSS Downloader IGS - CDDS")

# Subida del CSV (o carga directa)
ruta_csv = "igs_stations.csv"
df = pd.read_csv(ruta_csv, sep=";",header=0)

# Selección de estación
#estacion = st.selectbox("Selecciona estación", df["Site Name"])

st.subheader("Selecciona la estación y la fecha")

estacion = st.selectbox("Estación", df["Site Name"])
col1, col2, col3 = st.columns(3)
with col1:
    anio = st.number_input("Año", value=2025, step=1)
with col2:
    mes = st.number_input("Mes", value=5, min_value=1, max_value=12, step=1)
with col3:
    dia = st.number_input("Día", value=1, min_value=1, max_value=31, step=1)

# Botón de descarga
if st.button("Descargar archivos"):
    with st.spinner("Espere unos minutos ..."):
        session = SessionWithHeaderRedirection()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        try:
            zip_buffer, nombre_zip = download_file_zip(anio, mes, dia, estacion, session, guardar_zip_local=True)

            st.success("¡Descarga lista!")

            st.download_button(
                label="⬇️ Descargar ZIP",
                data=zip_buffer,
                file_name=nombre_zip,
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")


# Mostrar mapa
st.subheader("Mapa de Estaciones GNSS")
display_map(ruta_csv)

