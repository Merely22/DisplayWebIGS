def main():
    import streamlit as st
    from NGS.generate_date import fecha_a_doy
    from NGS.generate_files import (
        cargar_estaciones_local,
        estaciones_mas_cercanas,
        verificar_disponibilidad_rinex
    )

    st.title("📥 Descarga de Archivos - NOAA (NGS)")

    # --- Paso 1: Entradas del Usuario ---
    st.header("1. Busca tu ubicación")
    col1, col2, col3 = st.columns(3)
    with col1:
        # Los valores por defecto se dejan vacíos o con valores genéricos
        lat = st.number_input("Latitud", format="%.6f", value=None, placeholder="Ej: 41.369166")
    with col2:

        lon = st.number_input("Longitud", format="%.6f", value=None, placeholder="Ej: -101.927889")
    with col3:
        fecha = st.date_input("Selecciona una fecha")

    # Inicializar session_state para guardar las estaciones encontradas
    if 'df_cercanas' not in st.session_state:
        st.session_state.df_cercanas = None

    # Botón para buscar estaciones. Este es el primer punto de interacción.
    if st.button("Buscar estaciones cercanas"):
        if lat is None or lon is None:
            st.warning("Por favor, ingresa una latitud y longitud válidas.")
        else:
            with st.spinner("Buscando estaciones..."):
                try:
                    df = cargar_estaciones_local()
                    # Guardamos el resultado en session_state para que no se pierda
                    st.session_state.df_cercanas = estaciones_mas_cercanas(df, lat, lon)
                    st.success(f"Se encontraron {len(st.session_state.df_cercanas)} estaciones cercanas.")
                except Exception as e:
                    st.error(f"Ocurrió un error al buscar estaciones: {e}")
                    st.session_state.df_cercanas = None # Limpiar en caso de error

    # --- Paso 2: Selección de Estaciones (SOLO si ya se buscaron) ---
    # Este bloque solo se muestra si el paso anterior fue exitoso
    if st.session_state.df_cercanas is not None and not st.session_state.df_cercanas.empty:
        st.header("2. Selecciona las estaciones a verificar")
        
        # Usamos multiselect para que el usuario elija de la lista encontrada
        estaciones_a_verificar = st.multiselect(
            "Estaciones encontradas (elige hasta 5):",
            options=st.session_state.df_cercanas['station'].tolist(),
            max_selections=5
        )

        # --- Paso 3: Verificación y Descarga (el paso final) ---
        # El segundo botón, que depende de que el usuario haya seleccionado algo
        if st.button("Verificar disponibilidad y obtener enlaces"):
            if not estaciones_a_verificar:
                st.warning("Debes seleccionar al menos una estación para verificar.")
            else:
                with st.spinner("Verificando archivos en el servidor de NOAA..."):
                    try:
                        anio, doy = fecha_a_doy(str(fecha))
                        # Filtramos el dataframe para trabajar solo con las estaciones seleccionadas
                        df_seleccionadas = st.session_state.df_cercanas[
                            st.session_state.df_cercanas['station'].isin(estaciones_a_verificar)
                        ]
                        
                        df_resultado = verificar_disponibilidad_rinex(df_seleccionadas, anio, doy)

                        st.header("3. Resultados y enlaces de descarga")
                        st.dataframe(df_resultado[['station', 'Distancia_km', 'Disponible', 'URL']])
                        
                        # Crear una sección de descargas más limpia
                        st.subheader("Enlaces de descarga directa:")
                        enlaces_disponibles = 0
                        for _, row in df_resultado.iterrows():
                            if row['Disponible'] == "SI":
                                # Usamos st.link_button para un estilo más moderno
                                st.link_button(f"Descargar archivo de {row['station']}", row['URL'])
                                enlaces_disponibles += 1
                        
                        if enlaces_disponibles == 0:
                            st.info("No se encontraron archivos disponibles para las estaciones y fecha seleccionadas.")

                    except Exception as e:
                        st.error(f"Ocurrió un error al verificar la disponibilidad: {e}")

# Bloque de ejecución principal
if __name__ == "__main__":
    main()