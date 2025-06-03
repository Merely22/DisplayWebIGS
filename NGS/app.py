def main():
    import streamlit as st
    from NGS.generate_date import fecha_a_doy
    from NGS.generate_files import (
        cargar_estaciones_local,
        estaciones_mas_cercanas,
        verificar_disponibilidad_rinex
    )

    st.title("Descarga de archivos RINEX desde NOAA CORS")

    # Entrada de fecha y coordenadas
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha = st.date_input("Selecciona una fecha")
    with col2:
        lat = st.number_input("Latitud",value= 41.369166, format="%.6f")
    with col3:
        lon = st.number_input("Longitud",value= -101.927889, format="%.6f")

    if st.button("Buscar estaciones y verificar archivos"):
        with st.spinner("Procesando..."):
            try:
                df = cargar_estaciones_local()
                anio, doy = fecha_a_doy(str(fecha))
                df_cercanas = estaciones_mas_cercanas(df, lat, lon)
                df_resultado = verificar_disponibilidad_rinex(df_cercanas, anio, doy)

                st.subheader("Estaciones más cercanas y disponibilidad")
                st.dataframe(df_resultado[['SITEID', 'Latitude', 'Longitude', 'Distancia_km', 'Disponible', 'URL']])
                
                for _, row in df_resultado.iterrows():
                    if row['Disponible'] == "SI":
                        st.markdown(f"[Descargar {row['SITEID']}]({row['URL']})")

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")


if __name__ == "__main__":
    import sys
    sys.exit(main())