# módulo 4: visualizador_estaciones.py
import pandas as pd
import folium
import streamlit_folium as st_folium
import zipfile
import os
import streamlit as st
import plotly.express as px
from pathlib import Path

# Módulo 4: Visualizador de Estaciones
class VisualizadorEstaciones:
    def __init__(self, archivo_csv='igs_stations.csv'):
        self.archivo_csv = archivo_csv
        self.df_estaciones = self.cargar_estaciones()

    def cargar_estaciones(self):
        # Datos de ejemplo - reemplazar con tu CSV real
        datos = {
            'Site Name': ['AREG00PER', 'AREQ00PER']
        }
        return pd.DataFrame(datos)

    def mostrar_mapa(self):
        fig = px.scatter_geo(self.df_estaciones,
                            lat='Site Name',
                            lon='Site Name',
                            hover_name='Site Name',
                            hover_data=['Site Name'],
                            projection='natural earth',
                            title='Estaciones GNSS Disponibles')
        
        fig.update_geos(showcountries=True, countrycolor="Black",
                        showsubunits=True, subunitcolor="Blue",
                        lataxis_range=[-60, 20],
                        lonaxis_range=[-90, -30],
                        scope='south america')
        
        fig.update_traces(marker=dict(size=12, color='red'),
                          selector=dict(mode='markers'))
        
        st.plotly_chart(fig, use_container_width=True)

    def seleccionar_estacion(self):
        st.subheader("Seleccione una estación")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.mostrar_mapa()
        
        with col2:
            estacion = st.selectbox(
                "Estación GNSS",
                options=self.df_estaciones['Site Name'],
                format_func=lambda x: f"{x} - {self.df_estaciones[self.df_estaciones['Site Name'] == x]['Country/Region'].values[0]}"
            )
            st.write(f"**País:** {self.df_estaciones[self.df_estaciones['Site Name'] == estacion]['Country/Region'].values[0]}")
            st.write(f"**Coordenadas:** Lat {self.df_estaciones[self.df_estaciones['Site Name'] == estacion]['Latitude'].values[0]:.3f}, Lon {self.df_estaciones[self.df_estaciones['Site Name'] == estacion]['Longitude'].values[0]:.3f}")
        
        return estacion

    def comprimir_datos(self, estacion, fecha):
        carpeta = Path(f"data/{estacion}/{fecha}")
        zip_filename = f"data/{estacion}_{fecha}.zip"
        
        if not carpeta.exists():
            st.error("No hay datos para comprimir")
            return
        
        with st.spinner(f"Comprimiendo datos en {zip_filename}..."):
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(carpeta):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, carpeta.parent)
                        zipf.write(file_path, arcname)
        
        st.success("Compresión completada")
        return zip_filename