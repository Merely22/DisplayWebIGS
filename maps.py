import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.distance import geodesic
from streamlit_folium import st_folium
import streamlit as st

def display_map(path_igs, path_noaa):
    st.title("🌍 Visualización de Estaciones GNSS")

    # --- Carga y preparación de datos (solo se hace una vez) ---
    @st.cache_data
    def load_data(path_igs, path_noaa):
        df1 = pd.read_csv(path_igs)
        df2 = pd.read_csv(path_noaa)

        df1.columns = df1.columns.str.lower().str.strip()
        df2.columns = df2.columns.str.lower().str.strip()

        df1 = df1.rename(columns={"site name": "station", "latitude": "lat", "longitude": "lon"})
        df2 = df2.rename(columns={"siteid": "station", "y": "lat", "x": "lon"})
        
        df1["Source"] = "IGS Stations GNSS"
        df2["Source"] = "NOAA Stations GNSS"

        df_all = pd.concat([df1, df2], ignore_index=True).dropna(subset=['lat', 'lon'])
        
        df_all["popup"] = df_all.apply(
            lambda row: f"<b>Estación:</b> {row['station']}<br>"
                        f"<b>Fuente:</b> {row['Source']}<br>"
                        f"<b>Lat:</b> {row['lat']:.4f}, <b>Lon:</b> {row['lon']:.4f}",
            axis=1
        )
        return df_all

    df_all = load_data(path_igs, path_noaa)

    # --- Interfaz de usuario ---
    #st.markdown("### 📍 Ingresa tus coordenadas")
    col1, col2 = st.columns(2)
    with col1:
        # Usamos session_state para recordar las coordenadas
        user_lat = st.number_input("Latitud", value=st.session_state.get('user_lat', 4.60971), format="%.6f", key="user_lat")
    with col2:
        user_lon = st.number_input("Longitud", value=st.session_state.get('user_lon', -74.08175), format="%.6f", key="user_lon")

    # Botón para activar la búsqueda y el zoom
    search_button = st.button("Buscar estaciones más cercanas")

    # --- Creación del mapa base ---
    # Centrado general al inicio
    m = folium.Map(location=[20, 0], zoom_start=2)

    # --- CORRECCIÓN 1: Usar MarkerCluster para un rendimiento óptimo ---
    # Creamos un cluster para cada fuente de datos
    cluster_igs = MarkerCluster(name="IGS Stations").add_to(m)
    cluster_noaa = MarkerCluster(name="NOAA Stations").add_to(m)

    # Añadimos los puntos a sus respectivos clusters
    for _, row in df_all[df_all['Source'] == "IGS Stations"].iterrows():
        folium.CircleMarker(
            location=(row["lat"], row["lon"]), radius=5, color="blue", fill=True, fill_color="blue",
            fill_opacity=0.6, popup=folium.Popup(row["popup"], max_width=300)
        ).add_to(cluster_igs)

    for _, row in df_all[df_all['Source'] == "NOAA Stations"].iterrows():
        folium.CircleMarker(
            location=(row["lat"], row["lon"]), radius=5, color="green", fill=True, fill_color="green",
            fill_opacity=0.6, popup=folium.Popup(row["popup"], max_width=300)
        ).add_to(cluster_noaa)

    # --- Lógica de búsqueda y zoom (se activa con el botón) ---
    if search_button:
        user_coords = (user_lat, user_lon)
        
        # Calcular distancias y encontrar las 5 más cercanas
        df_all["Distancia_km"] = df_all.apply(lambda row: geodesic(user_coords, (row["lat"], row["lon"])).km, axis=1)
        estaciones_cercanas = df_all.nsmallest(5, "Distancia_km")

        st.markdown("### 📋 Las 5 estaciones más cercanas")
        st.dataframe(estaciones_cercanas[["station", "lat", "lon", "Distancia_km", "Source"]])

        # Capa para los marcadores rojos (cercanos)
        capa_cercanas = folium.FeatureGroup(name="Estaciones Cercanas", show=True).add_to(m)

        # Añadir marcador de usuario
        folium.Marker(
            user_coords,
            icon=folium.Icon(color='purple', icon='star'),
            popup="Tu ubicación"
        ).add_to(capa_cercanas)

        # Añadir marcadores de estaciones cercanas
        for _, row in estaciones_cercanas.iterrows():
            folium.Marker(
                location=(row["lat"], row["lon"]),
                icon=folium.Icon(color="red", icon="tower", prefix='fa'),
                popup=folium.Popup(f"<b>{row['station']}</b><br>Distancia: {row['Distancia_km']:.2f} km", max_width=300)
            ).add_to(capa_cercanas)

        # --- CORRECCIÓN 2: Zoom automático y dinámico ---
        # Creamos una lista de puntos para ajustar el mapa
        puntos_para_zoom = estaciones_cercanas[['lat', 'lon']].values.tolist()
        puntos_para_zoom.append(user_coords)
        m.fit_bounds(puntos_para_zoom, padding=(50, 50))

    # --- CORRECCIÓN 3: Leyenda bien posicionada ---
    legend_html = """
    <div style='position: absolute; top: 10px; right: 10px; width: 180px;
                background-color: rgba(255, 255, 255, 0.8); z-index: 1000; 
                padding: 10px; border: 1px solid grey; border-radius: 5px; font-size: 14px;'>
        <b>🗺️ Leyenda</b><br>
        <i class="fa fa-circle" style="color:blue"></i> IGS Stations GNSS<br>
        <i class="fa fa-circle" style="color:green"></i> NOAA Stations GNSS<br>
        <i class="fa fa-map-marker" style="color:red"></i> 5 más cercanas<br>
        <i class="fa fa-star" style="color:purple"></i> Tu ubicación
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Añadir control de capas
    folium.LayerControl().add_to(m)

    # --- Renderizar el mapa ---
    st.markdown("### 🌐 Mapa interactivo")
    st_folium(m, width=900, height=600, returned_objects=[])