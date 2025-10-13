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

# ---------------- Helpers para "cards" de estación ----------------

def _get_first(row: pd.Series, *candidates, default="—"):
    for c in candidates:
        if c in row and pd.notna(row[c]):
            return row[c]
    return default

def _fmt_latlon(row: pd.Series) -> str:
    lat = row.get("latitude", None)
    lon = row.get("longitude", None)
    try:
        if pd.notna(lat) and pd.notna(lon):
            return f"{float(lat):.6f}, {float(lon):.6f}"
    except Exception:
        pass
    return "—"

def _fmt_distance(row: pd.Series) -> str:
    d = row.get("distance_km", None)
    try:
        if pd.notna(d):
            return f"{float(d):.1f} km"
    except Exception:
        pass
    return "—"

def _render_station_cards(df_near: pd.DataFrame):
    if df_near is None or df_near.empty:
        return
    st.subheader("Station info")
    for i in range(0, len(df_near), 2):
        cols = st.columns(2)
        slice_df = df_near.iloc[i:i+2]
        for j, (_, r) in enumerate(slice_df.iterrows()):
            with cols[j]:
                station = _get_first(r, "station")
                city    = _get_first(r, "City", "city", "Town", "Location")
                country = _get_first(r, "Country", "country")
                latlon  = _fmt_latlon(r)
                dist    = _fmt_distance(r)
                carpeta = _get_first(r, "carpeta")
                tipo    = _get_first(r, "Tipo", "tipo")
                agency  = _get_first(r, "Station Owner", "agency", "Owner", "operator")
                domes   = _get_first(r, "Domes", "DOMES", "domes")
                monum   = _get_first(r, "TectonicPlate")

                st.markdown(
                    f"""
<div style="border:1px solid #e6e6e6;border-radius:12px;padding:12px;">
  <div style="font-weight:700;font-size:1.05rem;">{station}</div>
  <div style="color:#666;margin-bottom:6px;">
    {city} • {country}
  </div>
  <div style="font-size:0.95rem;line-height:1.35;">
    <b>Lat/Lon:</b> {latlon}<br/>
    <b>Distance:</b> {dist}<br/>
    <b>Folder:</b> {carpeta} &nbsp;&nbsp; <b>Tipo:</b> {tipo}<br/>
    <b>Agency:</b> {agency}<br/>
    <b>DOMES:</b> {domes}<br/>
    <b>Tectonic Plate:</b> {monum}
  </div>
</div>
                    """,
                    unsafe_allow_html=True
                )

# ---------------- App ----------------

def main():
    st.header("**📥 File Download - EUREF/IGS (EUROPE) High-Rate (RINEX 3)**")

    # ==== Sidebar: enlace + citación ====
    #with st.sidebar:
        #st.markdown("### 📍 EPN Coordinates (ETRS89/ETRF)")
        #st.markdown("[Open EPN Coordinates Portal](http://epncb.oma.be/_productsservices/coordinates/#Solution)")
        #st.markdown("---")
        #st.markdown("#### How to cite")
        #st.markdown(
            #"""
#**Please cite the EPN Multi-year Position and Velocity Solutions as:**

#Legrand J. (2022): *EPN multi-year position and velocity solution CWWWW*, Available from Royal Observatory of Belgium, https://doi.org/10.24414/ROB-EUREF-CWWWW.

#**A DOI is also available for each solution since solution C2085. Please cite the current multi-year solution as:**

#Legrand J. (2022): *EPN multi-year position and velocity solution C2235*, Available from Royal Observatory of Belgium, https://doi.org/10.24414/ROB-EUREF-C2235.
            #"""
        #)

    # --- Paso 1: Inputs ---
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

    if "df_cercanas_euref" not in st.session_state:
        st.session_state.df_cercanas_euref = None

    if st.button("Search nearest stations"):
        if lat is None or lon is None:
            st.warning("Please enter a valid latitude and longitude.")
        else:
            with st.spinner("Searching stations..."):
                try:
                    df = cargar_estaciones_local(EUREF_DB_PATH)
                    st.session_state.df_cercanas_euref = estaciones_mas_cercanas(df, lat, lon, n=4)
                    st.success(f"Found {len(st.session_state.df_cercanas_euref)} nearby stations.")
                    cols = ["station", "latitude", "longitude", "distance_km", "carpeta"]
                    cols = [c for c in cols if c in st.session_state.df_cercanas_euref.columns]
                    st.dataframe(st.session_state.df_cercanas_euref[cols], use_container_width=True)
                    _render_station_cards(st.session_state.df_cercanas_euref)
                except Exception as e:
                    st.error(f"Error while searching stations: {e}")
                    st.session_state.df_cercanas_euref = None

    # --- Paso 2: Selección (1–4) y descarga ---
    if st.session_state.df_cercanas_euref is not None and not st.session_state.df_cercanas_euref.empty:
        st.subheader("**Select stations to download**")
        opciones = st.session_state.df_cercanas_euref["station"].tolist()
        seleccion = st.multiselect("Choose 1–4 stations:", options=opciones, default=opciones[:1], max_selections=4)

        estaciones_tipo_S = None
        try:
            estaciones_tipo_S = cargar_estaciones_tipo_S(EUREF_DB_PATH)
        except Exception:
            pass

        if st.button("Download"):
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

            with st.spinner("Processing... "):
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

if __name__ == "__main__":
    main()
