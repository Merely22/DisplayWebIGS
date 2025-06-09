import pandas as pd
import streamlit as st

def mostrar_info_estacion_resumida(sitename, summary_dict, csv_df):
    csv_df.columns = csv_df.columns.str.strip()
    codigo = sitename[:4].upper()
    fila = csv_df[csv_df["estacion"].str.startswith(codigo)]
    if fila.empty:
        st.warning("No information was found in the local CSV.")
        return
    version_rinex = summary_dict.get(codigo, {}).get("Format", "N/A")

    agencia = fila["agencies"].values[0] if "agencies" in fila.columns else "N/A"
    constelaciones = fila["satellite system"].values[0] if "satellite system" in fila.columns else "N/A"
    resumen = pd.DataFrame([{
        "ID Station": codigo,
        "Name complete": fila["estacion"].values[0],
        "Approximate Position": f"{fila['latitud'].values[0]}, {fila['longitud'].values[0]}",
        "RINEX Version": version_rinex,
        "Interval (1s)": fila["rate 1s"].values[0],
        "Agencies": agencia,
        "Constellations": constelaciones
    }])
    st.markdown("**Summary of selected station**")
    st.dataframe(resumen)