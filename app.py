import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.express as px
import zipfile
import os
import requests
from datetime import datetime
import secrets 
####
from src.autenticador import AutenticadorEarthData
from src.generate_date import GeneradorFechas
from src.generate_files import GeneradorArchivos
from src.maps import VisualizadorEstaciones
###

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Descarga RINEX - IGS",
    page_icon="🛰️",
    layout="wide"
)

# Interfaz principal
def main():
    st.title("🛰️ Sistema de Descarga de Datos GNSS")
    st.markdown("""
    Esta aplicación permite descargar datos de alta frecuencia de estaciones GNSS del CDDIS NASA.
    """)
    
    # Inicializar clases
    visualizador = VisualizadorEstaciones()
    autenticador = AutenticadorEarthData()
    generador_archivos = GeneradorArchivos(autenticador._crear_sesion())
    generador_fechas = GeneradorFechas()

    # Sidebar con información
    st.sidebar.title("Opciones")
    st.sidebar.info("Seleccione una estación y fecha para descargar los datos")

    # Paso 1: Seleccionar estación
    estacion = visualizador.seleccionar_estacion()

    # Paso 2: Seleccionar fecha
    st.subheader("Seleccione la fecha")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        anio = st.number_input("Año", min_value=2000, max_value=datetime.now().year, value=2023)
    
    with col2:
        mes = st.number_input("Mes", min_value=1, max_value=12, value=1)
    
    with col3:
        dia = st.number_input("Día", min_value=1, max_value=31, value=1)

    # Calcular fechas
    dia_del_anio = generador_fechas.calcular_dia_anio(anio, mes, dia)
    fecha_texto = generador_fechas.obtener_fecha_formateada(anio, mes, dia)

    # Botón de descarga
    if st.button("Descargar Datos", type="primary"):
        with st.spinner("Preparando descarga..."):
            carpeta_salida = generador_archivos.crear_carpeta_salida(estacion, fecha_texto)
            vinculos = generador_archivos.obtener_vinculos(anio, dia_del_anio, estacion)
            
            st.info(f"Descargando {len(vinculos)} archivos para {estacion} - {fecha_texto}")
            
            progress_bar = st.progress(0)
            generador_archivos.descargar_archivos(vinculos, carpeta_salida, progress_bar)
            
            st.success("Descarga completada")

    # Comprimir resultados
    if st.button("Comprimir Datos"):
        zip_filename = visualizador.comprimir_datos(estacion, fecha_texto)
        if zip_filename:
            with open(zip_filename, "rb") as f:
                st.download_button(
                    label="Descargar ZIP",
                    data=f,
                    file_name=f"{estacion}_{fecha_texto}.zip",
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()