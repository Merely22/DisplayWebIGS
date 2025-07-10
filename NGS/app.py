def main():
    import streamlit as st
    from NGS.generate_date import fecha_a_doy
    from NGS.generate_files import (
        cargar_estaciones_local,
        estaciones_mas_cercanas,
        verificar_disponibilidad_rinex,
        crear_zip_rinex_y_coord
    )

    st.header("**📥 File Download  - NOAA (NGS)**")

    # --- Paso 1: Entradas del Usuario ---
    st.subheader("*Search your locations*")
    col1, col2, col3 = st.columns(3)
    with col1:
        # Los valores por defecto se dejan vacíos o con valores genéricos
        lat = st.number_input("Latitude", format="%.6f", value=None, placeholder="Ej: 41.369166")
    with col2:

        lon = st.number_input("Longitude", format="%.6f", value=None, placeholder="Ej: -101.927889")
    with col3:
        fecha = st.date_input("Select a date")

    # Inicializar session_state para guardar las estaciones encontradas
    if 'df_cercanas' not in st.session_state:
        st.session_state.df_cercanas = None

    # Botón para buscar estaciones. Este es el primer punto de interacción.
    if st.button("Search nearest stations"):
        if lat is None or lon is None:
            st.warning("Please, enter a valid latitude y longitude.")
        else:
            with st.spinner("Searching stations..."):
                try:
                    df = cargar_estaciones_local()
                    # Guardamos el resultado en session_state para que no se pierda
                    st.session_state.df_cercanas = estaciones_mas_cercanas(df, lat, lon)
                    st.success(f"Nearby {len(st.session_state.df_cercanas)} stations were found.")
                except Exception as e:
                    st.error(f"An error occurred while searching for stations: {e}")
                    st.session_state.df_cercanas = None # Limpiar en caso de error

    # --- Paso 2: Selección de Estaciones (SOLO si ya se buscaron) ---
    # Este bloque solo se muestra si el paso anterior fue exitoso
    if st.session_state.df_cercanas is not None and not st.session_state.df_cercanas.empty:
        st.subheader("**Select the stations to verify**")
        
        # Usamos multiselect para que el usuario elija de la lista encontrada
        estaciones_a_verificar = st.multiselect(
            "Seasons found (choose up to 5):",
            options=st.session_state.df_cercanas['Station'].tolist(),
            max_selections=5
        )

        # --- Paso 3: Verificación y Descarga (el paso final) ---
        # El segundo botón, que depende de que el usuario haya seleccionado algo
        if st.button("Check availability and get links"):
            if not estaciones_a_verificar:
                st.warning("You must select at least one station to verify.  ")
            else:
                with st.spinner("Verifying files on the NOAA server..."):
                    try:
                        anio, doy = fecha_a_doy(str(fecha))
                        # Filtramos el dataframe para trabajar solo con las estaciones seleccionadas
                        df_seleccionadas = st.session_state.df_cercanas[
                            st.session_state.df_cercanas['Station'].isin(estaciones_a_verificar)
                        ]
                        
                        df_resultado = verificar_disponibilidad_rinex(df_seleccionadas, anio, doy)

                        st.subheader("**Results and download links**")
                        st.dataframe(df_resultado[['Station', 'Distance_km', 'Available']])
                        
                        # Crear una sección de descargas más limpia
                        st.subheader("Direct download links:")
                        enlaces_disponibles = 0
                        for _, row in df_resultado.iterrows():
                            if row['Available'] == "YES":
                                try:
                                    zip_buffer = crear_zip_rinex_y_coord(row['Station'],  row['URL'], anio, doy)
                                    st.download_button(
                                        label=f"Download ZIP of {row['Station']}",
                                        data=zip_buffer,
                                        file_name=f"{row['Station'].lower()}_{anio}{doy}.zip",
                                        mime="application/zip"
                                    )
                                    enlaces_disponibles += 1
                                except Exception as e:
                                    st.error(f"Error downloading {row['Station']}: {e}")
                        if enlaces_disponibles == 0:
                            st.info("No files were found available for the selected stations and date.")

                    except Exception as e:
                        st.error(f"An error occurred while checking availability: {e}")

# Bloque de ejecución principal
##if __name__ == "__main__":
##    main()