def main ():
    import streamlit as st
    import pandas as pd
    import os 
    from datetime import datetime
    from IGS.authenticator import SessionWithHeaderRedirection
    from IGS.generate_files import download_file_zip
    from IGS.generate_date import calculate_date
    #from streamlit_option_menu import option_menu

    #st.set_page_config(layout="wide", page_title="GNSS NASA App")

    # Load station data
    data_path = "data/igs_stations.csv"
    df = pd.read_csv(data_path, sep=",", header=0)
    df.columns = df.columns.str.strip().str.lower()

    st.title("📥 Descarga de Archivos GNSS")

    estacion = st.selectbox("Estación", df["site name"].unique())
    st.write("Seleccione un intervalo de máximo 3 horas")
    col1, col2, col3 ,col4, col5 = st.columns(5)

    with col1:
        hora_inicio=st.number_input("Hora inicial (UTC): ", value=0, min_value=0, max_value=23, step=1)
    with col2:
        hora_fin=st.number_input("Hora final (UTC): ", value=24, min_value=0, max_value=24, step=1)
    with col3:
        dia = st.number_input("Día", value=1, min_value=1, max_value=31, step=1)
    with col4:
        mes = st.number_input("Mes", value=6, min_value=1, max_value=12, step=1)
    with col5:
        anio = st.number_input("Año", value=2025, min_value=2023, step=1)


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

if __name__ == "__main__":
    import sys
    sys.exit(main())