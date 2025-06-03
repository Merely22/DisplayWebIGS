def main ():
    import streamlit as st
    import pandas as pd
    import os 
    from datetime import datetime
    from IGS.authenticator import SessionWithHeaderRedirection
    from IGS.generate_files import download_file_zip, estaciones_mas_cercanas
    from IGS.generate_date import fecha_a_doy

    st.title("📡 Descarga de Archivos GNSS - NASA/CDDIS")

    # Paso 1: Ingreso de ubicación

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        fecha = st.date_input("Selecciona una fecha")
    with col2:
        hora_inicio = st.number_input("Hora inicial (UTC)", value=0, min_value=0, max_value=23, step=1)
    with col3:
        hora_fin = st.number_input("Hora final (UTC)", value=3, min_value=0, max_value=24, step=1)
    with col4:
        lat = st.number_input("Latitud", value=-12.0, format="%.4f")
    with col5:
        lon = st.number_input("Longitud", value=-77.0, format="%.4f")

    # Validar que el intervalo no exceda 3 horas
    data_path = "data/igs_stations.csv"
    df = pd.read_csv(data_path, sep=",", header=0)
    df.columns = df.columns.str.strip().str.lower()
    df.rename(columns={"latitude": "latitud", "longitude": "longitud", "site name": "estacion"}, inplace=True)
    #print(df.head(5))

    # Obtener estaciones cercanas
    estaciones_cercanas = estaciones_mas_cercanas(lat, lon, df, top_n=5)
    estaciones_seleccionadas = st.multiselect(
        "Estaciones más cercanas (elige hasta 2):",
        estaciones_cercanas["estacion"].tolist(),
        default=estaciones_cercanas["estacion"].tolist()[:1],
        max_selections=1
    )

    if st.button("Descargar archivos"):
        if hora_fin <= hora_inicio or hora_fin - hora_inicio > 3:
            st.warning("⚠️ El intervalo debe ser mayor a 0 y de máximo 3 horas.")
        elif len(estaciones_seleccionadas) == 0:
            st.warning("⚠️ Selecciona al menos una estación.")
        else:
            anio, doy = fecha_a_doy(str(fecha))
            for estacion in estaciones_seleccionadas:
                with st.spinner("Procesando..."):
                    resultado, mensaje, zip_path, temp_dir = download_file_zip(fecha, estacion, hora_inicio, hora_fin)
                    #st.subheader("Estaciones más cercanas")
                    #st.dataframe(df['estacion', 'latitud', 'longitud', 'Distancia_km'])
                    if resultado:
                        st.success(mensaje)
                        with open(zip_path, "rb") as f:
                            st.download_button(
                                f"Descargar ZIP de {estacion}",
                                f,
                                file_name=os.path.basename(zip_path),
                                mime="application/zip"
                            )
                        temp_dir.cleanup()
                    else:
                        st.warning(mensaje)


if __name__ == "__main__":
    import sys
    sys.exit(main())