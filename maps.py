import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.distance import geodesic
from streamlit_folium import st_folium
import streamlit as st
from folium import Element

def display_map(path_igs, path_noaa):
    st.title("🌍 Visualización de Estaciones GNSS")

    df1 = pd.read_csv(path_igs)
    df2 = pd.read_csv(path_noaa)

    df1.columns = df1.columns.str.lower().str.strip()
    df2.columns = df2.columns.str.lower().str.strip()

    # Entrada de coordenadas
    st.markdown("### 📍 Coordenadas de búsqueda")
    user_lat = st.number_input("Latitud", value=49.877017, format="%.6f")
    user_lon = st.number_input("Longitud", value=-97.047440, format="%.6f")
    user_coords = (user_lat, user_lon)

    # Preparar columnas comunes
    df1 = df1.rename(columns={"site name": "station","latitude": "lat", "longitude": "lon"})
    df2 = df2.rename(columns={"siteid": "station","y": "lat", "x": "lon"})
    df1["source"] = "IGS Staions GNSS"
    df2["source"] = "NOAA Staions GNSS"

    df1["popup"] = df1[["station", "lat", "lon"]].astype(str).agg("<br>".join, axis=1)
    df2["popup"] = df2[["station", "lat", "lon"]].astype(str).agg("<br>".join, axis=1)

    df_all = pd.concat([df1, df2], ignore_index=True)
    df_all["distancia"] = df_all.apply(lambda row: geodesic(user_coords, (row["lat"], row["lon"])).km, axis=1)

    estaciones_cercanas = df_all.nsmallest(5, "distancia")
    st.markdown("### 📋 Estaciones más cercanas")
    st.dataframe(estaciones_cercanas[["station", "lat", "lon", "distancia"]])

    # Mapa centrado inicialmente entre Sudamérica y Europa
    centro = user_coords if user_coords else [df_all['lat'].mean(), df_all['lon'].mean()]
    m = folium.Map(location=centro, zoom_start=5)
    #m = folium.Map(location=[0, -30], zoom_start=2)

    capa_csv1 = folium.FeatureGroup(name="IGS Stations GNSS", show=True)
    capa_csv2 = folium.FeatureGroup(name="NOAA Stations GNSS", show=True)
    capa_cercanas = folium.FeatureGroup(name="Estaciones Cercanas", show=True)

    for _, row in df1.iterrows():
        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=5,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.6,
            popup=folium.Popup(row["popup"], max_width=300)).add_to(capa_csv1)

    for _, row in df2.iterrows():
        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=5,
            color="green",
            fill=True,
            fill_color="green",
            fill_opacity=0.6,
            popup=folium.Popup(row["popup"], max_width=300)
        ).add_to(capa_csv2)

    for _, row in estaciones_cercanas.iterrows():
        folium.Marker(
            location=(row["lat"], row["lon"]),
            icon=folium.Icon(color="red"),
            popup=folium.Popup(f"Distancia: {row['distancia']:.2f} km<br>{row['popup']}", max_width=300)
        ).add_to(capa_cercanas)

    folium.Marker(
        user_coords,
        icon=folium.Icon(color='purple', icon='&#xf041'),
        popup="Ubicación del usuario"
    ).add_to(m)

    # Agregar leyenda
    legend_html = """
    <div style='position: fixed;'color: black'; bottom: 50px; left: 50px; z-index: 9999; 
                background-color: white; padding: 10px; border:2px solid gray;'>
        <b>🗺️ Leyenda</b><br>
        🔵 Estaciones IGS  GNSS<br>
        🟢 Estaciones NOAA  GNSS<br>
        🔴 Las 5 más cercanas<br>
        ⭐ Tu ubicación
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    m.add_child(capa_csv1)
    m.add_child(capa_csv2)
    m.add_child(capa_cercanas)
    folium.LayerControl().add_to(m)

    st.markdown("### 🌐 Mapa interactivo")
    st_folium(m, width=900, height=600)


