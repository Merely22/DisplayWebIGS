import pandas as pd
import folium
from folium.plugins import MarkerCluster

def display_map(ruta_csv, user_coords=None, nearest_stations=[]):
    df = pd.read_csv(ruta_csv, sep=";", header=0)
    df.columns = df.columns.str.strip().str.lower()

    centro = user_coords if user_coords else [df['latitude'].mean(), df['longitude'].mean()]
    mapa = folium.Map(location=centro, zoom_start=5)
    marker_cluster = MarkerCluster().add_to(mapa)

    for _, row in df.iterrows():
        Lat = row['latitude']
        Lon = row['longitude']
        Estacion = row['site name']
        Elevacion = row.get('height(m)', 'Unknown')
        Region = row.get('country/region', 'Unknown')
        Last_data = row.get('last data','Unknown')
        Receptor = row.get('receiver', 'Unknown')
        Antena = row.get('antenna', 'Unknown')
        Sistema = row.get('satellite system', 'Unknown')
        color = "green" if Last_data != 'Unknown' else "red"
        popup_html = f"""
        <b>{Estacion}</b><br>
        <b>Latitude, Longitude:</b> {Lat}, {Lon}<br>
        <b>Elevation:</b> {Elevacion} m<br>
        <b>Country/Region:</b> {Region}<br>
        <b>Last Data:</b> <span style='background-color:{color}; color:white; padding:2px 4px; border-radius:4px;'>{Last_data}</span><br>
        <b>Receiver:</b> {Receptor}<br>
        <b>Antenna:</b> {Antena}<br>
        <b>Satellite System:</b> {Sistema}<br>
        """
        color_marker = "blue" if Estacion in nearest_stations else color
        folium.Marker(location=[Lat, Lon], popup=popup_html, icon=folium.Icon(color=color_marker)).add_to(marker_cluster)

    if user_coords:
        folium.Marker(user_coords, icon=folium.Icon(color='purple'), popup="Your location").add_to(mapa)

    return mapa
