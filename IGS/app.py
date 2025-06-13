import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import os
from pathlib import Path
from IGS.generate_files import download_file_zip, estaciones_mas_cercanas
from IGS.components import mostrar_info_estacion_resumida
from IGS.sumary_checker import descargar_summary, parsear_summary, verificar_disponibilidad_summary, obtener_formato_rinex

def main():
    st.header("**📥 File Download - International GNSS Service (IGS)**")

    # --- Carga de datos inicial (usando caché para eficiencia) ---
    @st.cache_data
    def load_station_data(path):
        try:
            df = pd.read_csv(path, sep=",", header=0)
            df.columns = df.columns.str.strip().str.lower()
            df.rename(columns={"latitude": "latitud", "longitude": "longitud", "site name": "estacion"}, inplace=True)
            return df
        except FileNotFoundError:
            return None
        
    RUTA_CRX2RNX=Path("data/CRX2RNX.exe")
    df_stations = load_station_data("data/igs_stations.csv")

    if df_stations is None:
        st.error("File ‘data/igs_stations.csv’ was not found. The application cannot continue.")
        return

    # --- Inicializar Session State para guardar datos entre pasos ---
    if 'verification_results' not in st.session_state:
        st.session_state.verification_results = None

    # --- Paso 1: Entradas del Usuario ---
    st.subheader("**Define search parameters**")
    col1, col2, col3 = st.columns(3)
    with col1:
        lat = st.number_input("Latitude", value=None, format="%.6f", placeholder="Ej: 49.877017")
    with col2:
        lon = st.number_input("Longitude", value=None, format="%.6f", placeholder="Ej: -97.047440")
    with col3:
        fecha_input = st.date_input("Date", value=datetime.now(timezone.utc).date())

    col4, col5 = st.columns(2)
    with col4:
        hora_inicio = st.number_input("Start time (UTC)", 0, 23, 0, 1)
    with col5:
        hora_fin = st.number_input("Final time (UTC)", 1, 24, 3, 1)

    # --- Paso 2: Botón de Búsqueda y Verificación ---
    if st.button("Search for stations and check availability"):
        if lat is None or lon is None:
            st.warning("Please, enter a valid latitude and longitude")
        else:
            with st.spinner("Searching for stations and contacting NASA's server..."):
                try:
                    # Encontrar estaciones cercanas
                    df_cercanas = estaciones_mas_cercanas(lat, lon, df_stations, top_n=5)
                    
                    # Verificar disponibilidad para estas estaciones
                    fecha_utc = datetime.combine(fecha_input, datetime.min.time(), tzinfo=timezone.utc)
                    summary_raw = descargar_summary(fecha_utc.year)
                    summary_dict = parsear_summary(summary_raw)
                    
                    results = []
                    for _, row in df_cercanas.iterrows():
                        estacion = row['estacion']
                        disponible, mensaje = verificar_disponibilidad_summary(estacion, fecha_utc, summary_dict, df_stations)
                        rinex_v = obtener_formato_rinex(estacion, summary_dict) if disponible else None
                        results.append({
                            "Station": estacion,
                            "Distance_km": row['distancia_km'],
                            "Available": disponible,
                            "Mesagge": mensaje,
                            "Rinex_version": rinex_v
                        })
                    
                    # Guardar los resultados en session_state para usarlos después
                    st.session_state.verification_results = pd.DataFrame(results)
                    st.success("Verification completed.")

                except Exception as e:
                    st.error(f"An error occurred during verification:: {e}")
                    st.session_state.verification_results = None

    # --- Paso 3: Selección y Descarga (solo si el paso 2 fue exitoso) ---
    if st.session_state.verification_results is not None:
        st.subheader("**Results and file download**")
        
        df_results = st.session_state.verification_results
        
        # Mostrar tabla de resultados de la verificación
        st.subheader("Availability of stations found")
        st.dataframe(df_results[['Station', 'Distance_km', 'Available', 'Mesagge']], use_container_width=True)

        # Filtrar solo las estaciones que SÍ están disponibles
        estaciones_disponibles = df_results[df_results['Available'] == True]['Station'].tolist()

        if not estaciones_disponibles:
            st.info("None of the nearby stations have data available for the selected date..")
        else:
            st.subheader("Select the stations to download")
            estaciones_a_descargar = st.multiselect(
                "You can download files for the following stations:",
                options=estaciones_disponibles,
                default=estaciones_disponibles # Por defecto, todas las disponibles
            )

            # Botón final para la acción de descarga
            if st.button("Download selected files"):
                if not estaciones_a_descargar:
                    st.warning("You must select at least one station to download.")
                elif hora_fin <= hora_inicio:
                    st.warning("⚠️ The end time must be greater than the start time.")
                elif hora_fin - hora_inicio > 3:
                    st.warning("⚠️ The interval cannot be more than 3 hours.")
                else:
                    fecha_dt = datetime.combine(fecha_input, datetime.min.time())
                    for estacion in estaciones_a_descargar:
                        # Recuperar la versión de rinex guardada
                        rinex_version = df_results.loc[df_results['Station'] == estacion, 'Rinex_version'].iloc[0]
                        
                        st.markdown(f"--- \n#### Processing `{estacion}`...")
                        with st.spinner(f"Generating ZIP for {estacion}..."):
                            resultado, mensaje, zip_path, temp_dir = download_file_zip(
                                fecha_dt, estacion, hora_inicio, hora_fin, rinex_version
                            )
                            
                            if resultado and zip_path:
                                st.success(f"✅ {mensaje}")
                                with open(zip_path, "rb") as f:
                                    st.download_button(
                                        f" {estacion}",
                                        data=f,
                                        file_name=os.path.basename(zip_path),
                                        mime="application/zip"
                                    )
                                if temp_dir:
                                    temp_dir.cleanup()
                            else:
                                st.error(f"⚠️ {mensaje}")

# Bloque de ejecución principal
##if __name__ == "__main__":
##    main()
