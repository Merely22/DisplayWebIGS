import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.distance import geodesic

st.set_page_config(layout="wide")
st.title("🛰️ Visualización de Estaciones GNSS desde CSV (con búsqueda por coordenadas)")

# Carga de archivos CSV locales
col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("📄 Cargar primer CSV", type="csv", key="csv1")
with col2:
    file2 = st.file_uploader("📄 Cargar segundo CSV", type="csv", key="csv2")

if file1 and file2:
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    st.markdown("### 🔧 Mapeo de columnas para coordenadas")
    with st.expander("Seleccionar columnas de latitud y longitud"):
        col_lat1 = st.selectbox("Latitud CSV 1", df1.columns)
        col_lon1 = st.selectbox("Longitud CSV 1", df1.columns)
        col_lat2 = st.selectbox("Latitud CSV 2", df2.columns)
        col_lon2 = st.selectbox("Longitud CSV 2", df2.columns)

        popup_attrs_1 = st.multiselect("Atributos a mostrar en popups (CSV 1)", df1.columns)
        popup_attrs_2 = st.multiselect("Atributos a mostrar en popups (CSV 2)", df2.columns)

    # Añadir columnas comunes para combinación
    df1["lat"] = df1[col_lat1]
    df1["lon"] = df1[col_lon1]
    df1["source"] = "CSV 1"
    df1["popup"] = df1[popup_attrs_1].astype(str).agg("<br>".join, axis=1)

    df2["lat"] = df2[col_lat2]
    df2["lon"] = df2[col_lon2]
    df2["source"] = "CSV 2"
    df2["popup"] = df2[popup_attrs_2].astype(str).agg("<br>".join, axis=1)

    # Unir ambos DataFrames
    df_all = pd.concat([df1, df2], ignore_index=True)

    st.markdown("### 📌 Ingresar coordenadas para buscar estaciones cercanas")
    col_lat, col_lon = st.columns(2)
    with col_lat:
        user_lat = st.number_input("Latitud", value=-12.0)
    with col_lon:
        user_lon = st.number_input("Longitud", value=-77.0)

    # Calcular las 5 estaciones más cercanas
    df_all["distancia_km"] = df_all.apply(
        lambda row: geodesic((user_lat, user_lon), (row["lat"], row["lon"])).km,
        axis=1
    )
    estaciones_cercanas = df_all.nsmallest(5, "distancia_km")

    # Crear el mapa
    mapa = folium.Map(location=[10, -30], zoom_start=3)
    capa_csv1 = folium.FeatureGroup(name="CSV 1", show=True)
    capa_csv2 = folium.FeatureGroup(name="CSV 2", show=True)
    capa_cercanas = folium.FeatureGroup(name="📍 5 Estaciones más cercanas", show=True)

    for _, row in df_all.iterrows():
        color = "blue" if row["source"] == "CSV 1" else "green"
        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(row["popup"], max_width=300)
        ).add_to(capa_csv1 if row["source"] == "CSV 1" else capa_csv2)

    for _, row in estaciones_cercanas.iterrows():
        folium.Marker(
            location=(row["lat"], row["lon"]),
            icon=folium.Icon(color="red", icon="info-sign"),
            popup=folium.Popup(f"Distancia: {row['distancia_km']:.2f} km<br>{row['popup']}", max_width=300)
        ).add_to(capa_cercanas)

    # Agregar leyenda manual
    legend_html = """
    <div style='position: fixed; bottom: 50px; left: 50px; z-index: 9999; 
                background-color: white; padding: 10px; border:2px solid gray;'>
        <b>🗺️ Leyenda</b><br>
        🔵 Estaciones CSV 1<br>
        🟢 Estaciones CSV 2<br>
        📍 Marcador rojo: 5 más cercanas
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(legend_html))

    # Agregar capas al mapa
    mapa.add_child(capa_csv1)
    mapa.add_child(capa_csv2)
    mapa.add_child(capa_cercanas)
    folium.LayerControl().add_to(mapa)

    st.markdown("### 🌐 Mapa interactivo")
    st_folium(mapa, width=1000, height=600)

else:
    st.info("Por favor, carga ambos archivos CSV para continuar.")
