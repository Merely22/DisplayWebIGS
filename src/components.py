import pandas as pd
import streamlit as st

def mostrar_info_estacion_resumida(sitename, summary_dict, csv_df):
    codigo = sitename[:4].upper()
    fila = csv_df[csv_df["Site Name"].str.startswith(codigo)]

    if fila.empty:
        st.warning("No se encontró información en el CSV local.")
        return

    version_rinex = summary_dict.get(codigo, {}).get("Format", "N/A")
    resumen = pd.DataFrame([{
        "ID Estación": codigo,
        "Nombre completo": fila["Site Name"].values[0],
        "Posición Aproximada": f"{fila['Latitude'].values[0]}, {fila['Longitude'].values[0]}",
        "Versión RINEX": version_rinex,
        "Intervalo (1s)": fila["Rate 1s"].values[0],
        "Agencia": fila.get("Agency", "N/A") if "Agency" in fila else "N/A",
        "Constelaciones": fila.get("Constellations", "N/A") if "Constellations" in fila else "N/A"
    }])

    st.markdown("📋 **Resumen de estación seleccionada**")
    st.dataframe(resumen)