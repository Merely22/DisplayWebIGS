def main():
    import streamlit as st
    from NGS.generate_date import fecha_a_doy
    from NGS.generate_files import (
        cargar_estaciones_local,
        estaciones_mas_cercanas,
        verificar_disponibilidad_rinex
    )

    st.title("Download Precise Orbits")

    # Entrada de fecha y coordenadas
    col1 = st.columns(1)
    with col1:
        fecha = st.date_input("Selecciona una fecha")