import folium
from folium import Popup, Icon
from folium.plugins import MarkerCluster, Search
import pandas as pd
from streamlit_folium import folium_static
import streamlit as st

def display_map(ruta_csv):
    df = pd.read_csv(ruta_csv, sep=";", header=0)

    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # Crear mapa base centrado en Sudamérica
    mapa = folium.Map(location=[-10, -55], zoom_start=4, tiles="OpenStreetMap")

    # Crear clúster de marcadores
    marker_cluster = MarkerCluster().add_to(mapa)

    for _, row in df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        estacion = row['site name']
        elevacion = row.get('elevation', 'N/A')
        region = row.get('country/region', 'Unknown')
        last_date = row.get('last data available','Unknown')
        receptor = row.get('receiver', 'Unknown')
        antena = row.get('antenna', 'Unknown')
        sistema = row.get('satellite system', 'Unknown')

        # Color por disponibilidad
        color = "green" if last_date == 'Unknown' else "red"

        # popup estilizado
        html_popup = f"""
        <b>{estacion}</b><br>
        <b>Latitude, Longitude:</b> {lat}, {lon}<br>
        <b>Elevation:</b> {elevacion} m<br>
        <b>Country/Region:</b> {region}<br>
        <b>Last Data Available:</b> <span style='background-color:#28a745; color:white; padding:2px 4px; border-radius:4px;'>{last_date}</span><br>
        <b>Receiver:</b> {receptor}<br>
        <b>Antenna:</b> {antena}<br>
        <b>Satellite System:</b> {sistema}<br></a>
        """

        popup = Popup(html_popup, max_width=300)
        icon = Icon(color=color, icon="	fas fa-map-marker-alt")

        folium.Marker(
            location=[lat, lon],
            popup=popup,
            tooltip=estacion,
            icon=icon
        ).add_to(marker_cluster)

    # Agregar búsqueda
    #Search(layer=marker_cluster, search_label='site name', placeholder='Buscar estación...').add_to(mapa)

    # Mostrar mapa en Streamlit
    folium_static(mapa)
