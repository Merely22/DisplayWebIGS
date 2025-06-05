import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import os
from IGS.generate_files import download_file_zip, estaciones_mas_cercanas
from IGS.components import mostrar_info_estacion_resumida
from IGS.generate_date import fecha_a_doy
from IGS.sumary_checker import descargar_summary, parsear_summary, verificar_disponibilidad_summary, obtener_formato_rinex

def main():
    st.title("📥 Descarga de Archivos GNSS")

    # --- Carga inicial de datos ---
    data_path = "data/igs_stations.csv"
    try:
        df = pd.read_csv(data_path, sep=",", header=0)
        df.columns = df.columns.str.strip().str.lower()
        df.rename(columns={"latitude": "latitud", "longitude": "longitud", "site name": "estacion"}, inplace=True)
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo de estaciones en la ruta: {data_path}")
        st.info("Asegúrate de que la carpeta 'data' y el archivo 'igs_stations.csv' estén en el lugar correcto.")
        return # Detiene la ejecución si el archivo no existe

    # --- Entradas del usuario ---
    col1, col2, col3 = st.columns(3)
    with col1:
        lat = st.number_input("Latitud", value=49.877017, format="%.4f")
    with col2:
        lon = st.number_input("Longitud", value=-97.047440, format="%.4f")
    with col3:
        fecha_input = st.date_input("Fecha", value=datetime.now(timezone.utc).date())

    col4, col5 = st.columns(2)
    with col4:
        hora_inicio = st.number_input("Hora inicial (UTC)", value=0, min_value=0, max_value=23, step=1)
    with col5:
        hora_fin = st.number_input("Hora final (UTC)", value=3, min_value=0, max_value=24, step=1)

    # --- Selección de estaciones ---
    st.markdown("---")
    estaciones_cercanas = estaciones_mas_cercanas(lat, lon, df, top_n=5)
    estaciones_seleccionadas = st.multiselect(
        "Estaciones más cercanas (elige hasta 2):",
        options=estaciones_cercanas["estacion"].tolist(),
        default=estaciones_cercanas["estacion"].tolist()[:2],
        max_selections=2
    )

    # Validación ahora se hace para cada estación seleccionada.
    # Esta sección se ejecuta solo si se han seleccionado estaciones.
    if estaciones_seleccionadas:
        st.markdown("---")
        st.subheader("Información y Disponibilidad")
        try:
            # Convertir la fecha una sola vez
            fecha = datetime.combine(fecha_input, datetime.min.time(), tzinfo=timezone.utc)
            anio_consulta = fecha.year

            # Descargar y parsear el summary una sola vez
            df_summary_raw = descargar_summary(anio_consulta)
            df_summary = parsear_summary(df_summary_raw)

            # Iterar sobre las estaciones que el usuario eligió
            for estacion in estaciones_seleccionadas:
                st.markdown(f"#### Estación: `{estacion}`")
                
                # Mostrar resumen
                mostrar_info_estacion_resumida(estacion, df_summary, df)

                # Verificar disponibilidad
                disponible, mensaje_dispo = verificar_disponibilidad_summary(estacion, fecha, df_summary, df)
                if disponible:
                    st.success(f"✔️ {mensaje_dispo}")
                else:
                    st.warning(f"❌ {mensaje_dispo}")

        except Exception as e:
            st.error(f"No se pudo verificar la disponibilidad: {e}")
            st.warning("Puede ser un problema de conexión o un error al contactar el servidor de la NASA.")

    # --- Botón de descarga ---
    if st.button("Descargar archivos"):
        if hora_fin <= hora_inicio:
            st.warning("⚠️ La hora final debe ser mayor que la hora inicial.")
        elif hora_fin - hora_inicio > 3:
            st.warning("⚠️ El intervalo no puede ser de más de 3 horas.")
        elif not estaciones_seleccionadas:
            st.warning("⚠️ Debes seleccionar al menos una estación.")
        else:
            fecha_dt = datetime.combine(fecha_input, datetime.min.time()) # Convertir a datetime
            for estacion in estaciones_seleccionadas:
                st.markdown(f"--- \n ### Procesando `{estacion}`...")
                with st.spinner(f"Descargando y convirtiendo archivos para {estacion}..."):
                    
                    # Se necesita la versión de RINEX para la descarga
                    df_summary_raw = descargar_summary(fecha_dt.year)
                    df_summary = parsear_summary(df_summary_raw)
                    rinex_version = obtener_formato_rinex(estacion, df_summary)

                    if not rinex_version:
                        st.error(f"No se pudo determinar la versión de RINEX para {estacion}. No se puede continuar.")
                        continue # Pasa a la siguiente estación

                    resultado, mensaje, zip_path, temp_dir = download_file_zip(
                        fecha_dt, estacion, hora_inicio, hora_fin, rinex_version
                    )
                    
                    if resultado and zip_path:
                        st.success(f"✅ {mensaje}")
                        with open(zip_path, "rb") as f:
                            st.download_button(
                                f"Descargar ZIP de {estacion}",
                                f,
                                file_name=os.path.basename(zip_path),
                                mime="application/zip"
                            )
                        if temp_dir:
                            temp_dir.cleanup() # Limpiar archivos temporales
                    else:
                        st.error(f"⚠️ {mensaje}")

if __name__ == "__main__":
    import sys
    sys.exit(main())