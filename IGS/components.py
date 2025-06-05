import pandas as pd
import streamlit as st

def mostrar_info_estacion_resumida(sitename, summary_dict, csv_df):
    csv_df.columns = csv_df.columns.str.strip()
    codigo = sitename[:4].upper()
    fila = csv_df[csv_df["estacion"].str.startswith(codigo)]
    if fila.empty:
        st.warning("No se encontró información en el CSV local.")
        return
    version_rinex = summary_dict.get(codigo, {}).get("Format", "N/A")

    agencia = fila["agencies"].values[0] if "agencies" in fila.columns else "N/A"
    constelaciones = fila["satellite system"].values[0] if "satellite system" in fila.columns else "N/A"
    resumen = pd.DataFrame([{
        "ID Estación": codigo,
        "Nombre completo": fila["estacion"].values[0],
        "Posición Aproximada": f"{fila['latitud'].values[0]}, {fila['longitud'].values[0]}",
        "Versión RINEX": version_rinex,
        "Intervalo (1s)": fila["rate 1s"].values[0],
        "Agencia": agencia,
        "Constelaciones": constelaciones
    }])
    st.markdown("**Resumen de estación seleccionada**")
    st.dataframe(resumen)