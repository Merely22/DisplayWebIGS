from __future__ import annotations
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date

from .generate_date import calculate_date, is_within_range
from .generate_files import (
    cargar_estaciones_local,
    cargar_estaciones_tipo_S,
    estaciones_mas_cercanas,
    descargar_y_procesar_estacion,
    combinar_zips_estaciones,
)

EUREF_DB_PATH = "data/EUREF_High-Rate.csv"  # CSV ya generado (filtrado + Tipo + Carpeta)

# ---------------- Cards helpers ----------------

def _pick(row, *candidates, fmt=None, default="—"):
    """Devuelve el primer campo existente en row, con formato opcional."""
    for c in candidates:
        if c in row and pd.notna(row[c]):
            v = row[c]
            return fmt(v) if fmt else v
    return default

def _render_station_cards(df_near: pd.DataFrame):
    """Muestra cards con info clave por estación (2 columnas por fila)."""
    if df_near is None or df_near.empty: 
        return
    st.subheader("Station info")
    # 2 cards por fila
    for i in range(0, len(df_near), 2):
        cols = st.columns(2)
        slice_df = df_near.iloc[i:i+2]
        for j, (_, r) in enumerate(slice_df.iterrows()):
            with cols[j]:
                st.markdown(
                    f"""
<div style="border:1px solid #e6e6e6;border-radius:12px;padding:12px;">
  <div style="font-weight:700;font-size:1.05rem;">{_pick(r, 'station')}</div>
  <div style="color:#666;margin-bottom:6px;">
    {_pick(r, 'City', 'city', 'Town', 'Location')} • {_pick(r, 'Country', 'country')}
  </div>
  <div style="font-size:0.95rem;line-height:1.35;">
    <b>Lat/Lon:</b> {_pick(r, 'latitude'):.6f}, {_pick(r, 'longitude'):.6f}<br/>
    <b>Distance:</b> {_pick(r, 'distance_km', fmt=lambda x: f"{x:.1f} km")}<br/>
    <b>Folder:</b> {_pick(r, 'carpeta')} &nbsp;&nbsp; <b>Tipo:</b> {_pick(r, 'Tipo', 'tipo')}<br/>
    <b>Agency:</b> {_pick(r, 'Agency', 'agency', 'Owner', 'operator')}<br/>
    <b>DOMES:</b> {_pick(r, 'Domes', 'DOMES', 'domes')}<br/>
    <b>Monument:</b> {_pick(r, 'Monument', 'monument')}
  </div>
</div>
                    """,
                    unsafe_allow_html=True
                )

def main():
    st.header("**📥 File Download - EUREF/IGS (EUROPE) High-Rate (RINEX 3)**")

    # --- Paso 1: Entradas ---
    st.subheader("*Search your locations*")
    c1, c2, c3 = st.columns(3)
    with c1:
        lat = st.number_input("Latitude", format="%.6f", value=None, placeholder="Ej: 48.8566")
    with c2:
        lon = st.number_input("Longitude", format="%.6f", value=None, placeholder="Ej: 2.35222")
    with c3:
        fecha = st.date_input("Select a date", date.today())

    c4, c5 = st.columns(2)
    with c4:
        hora_inicio = st.number_input("Start hour (0–23)", min_value=0, max_value=23, value=0, step=1)
    with c5:
        hora_fin = st.number_input("End hour (exclusive, 1–24)", min_value=1, max_value=24, value=24, step=1)

    # Estado
    if "df_cercanas_euref" not in st.session_state:
        st.session_state.df_cercanas_euref = None

    # Buscar 4 más cercanas (sin check availability ni links)
    if st.button("Search nearest stations"):
        if lat is None or lon is None:
            st.warning("Please enter a valid latitude and longitude.")
        else:
            with st.spinner("Searching stations..."):
                try:
                    df = cargar_estaciones_local(EUREF_DB_PATH)  # incluye carpeta/tipo si existen
                    st.session_state.df_cercanas_euref = estaciones_mas_cercanas(df, lat, lon, n=4)
                    st.success(f"Found {len(st.session_state.df_cercanas_euref)} nearby stations.")
                    cols = ["station", "latitude", "longitude", "distance_km", "carpeta"]
                    cols = [c for c in cols if c in st.session_state.df_cercanas_euref.columns]
                    st.dataframe(st.session_state.df_cercanas_euref[cols])
                    _render_station_cards(st.session_state.df_cercanas_euref)
                except Exception as e:
                    st.error(f"Error while searching stations: {e}")
                    st.session_state.df_cercanas_euref = None

    # --- Paso 2: Selección (1–4) y descarga ---
    if st.session_state.df_cercanas_euref is not None and not st.session_state.df_cercanas_euref.empty:
        st.subheader("**Select stations to download/merge**")
        opciones = st.session_state.df_cercanas_euref["station"].tolist()
        seleccion = st.multiselect("Choose 1–4 stations:", options=opciones, default=opciones[:1], max_selections=4)

        # Set de 'S' si el CSV trae columna Tipo (auto); si no, backend intentará S y R
        estaciones_tipo_S = None
        try:
            estaciones_tipo_S = cargar_estaciones_tipo_S(EUREF_DB_PATH)
        except Exception:
            pass

        if st.button("Download, convert (CRX→RNX) and merge"):
            if not seleccion:
                st.warning("Select at least one station.")
                return

            ok_rango, diff = is_within_range(fecha)
            if not ok_rango:
                st.warning(f"⚠️ The date is {diff} days old (>182). Files may not be present.")
            doy = calculate_date(fecha.year, fecha.month, fecha.day)

            df_n = st.session_state.df_cercanas_euref
            zips: list[tuple[str, BytesIO]] = []
            logs = []

            with st.spinner("Processing... (download → CRX2RNX → GFZRNX)"):
                for stn in seleccion:
                    carpeta = df_n.loc[df_n["station"] == stn, "carpeta"].iloc[0] if "carpeta" in df_n.columns else "IGS"
                    ok, msg, zipbuf = descargar_y_procesar_estacion(
                        station=stn,
                        anio=fecha.year,
                        doy=doy,
                        hora_inicio=int(hora_inicio),
                        hora_fin=int(hora_fin),
                        estaciones_tipo_S=estaciones_tipo_S,
                        carpeta=carpeta
                    )
                    logs.append(msg)
                    if ok:
                        zips.append((stn, zipbuf))

            st.subheader("Log")
            for line in logs:
                st.write("• " + line)

            if not zips:
                st.error("No station produced output.")
                return

            # 1 estación → 1 ZIP ; 2–4 → ZIP combinado
            if len(zips) == 1:
                stn, buf = zips[0]
                st.download_button(
                    label=f"Download ZIP of {stn}",
                    data=buf.getvalue(),
                    file_name=f"{stn}_{fecha.strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                )
            else:
                combo = combinar_zips_estaciones(zips)
                st.download_button(
                    label=f"Download combined ZIP ({len(zips)} stations)",
                    data=combo.getvalue(),
                    file_name=f"EUREF_{fecha.strftime('%Y%m%d')}_{int(hora_inicio):02d}-{int(hora_fin):02d}.zip",
                    mime="application/zip",
                )

# Ejecutable directo (si no lo importas en tu main de Streamlit)
if __name__ == "__main__":
    # No llames st.set_page_config aquí si lo importas en tu main.py
    main()
