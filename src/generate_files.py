# módulo 3: generador_archivos.py
from pathlib import Path
import requests
import os
import streamlit as st

# Módulo 3: Generador de Archivos
class GeneradorArchivos:
    def __init__(self, session):
        self.session = session

    def obtener_vinculos(self, anio, dia_del_anio_formateado, estacion):
        urls = []
        for hora in range(24):
            subcarpeta = f"{hora:02d}"
            for minuto in range(0, 60, 15):
                h = f"{hora:02d}"
                m = f"{minuto:02d}"
                nombre_archivo = f"{estacion}_R_{anio}{dia_del_anio_formateado}{h}{m}_15M_01S_MO.crx.gz"
                url = (f"https://cddis.nasa.gov/archive/gnss/data/highrate/"
                       f"{anio}/{dia_del_anio_formateado}/25d/{subcarpeta}/{nombre_archivo}")
                urls.append((url, nombre_archivo))
        return urls

    def descargar_archivos(self, vinculos, carpeta_salida, progress_bar):
        total = len(vinculos)
        for i, (url, nombre_archivo) in enumerate(vinculos):
            ruta_destino = carpeta_salida / nombre_archivo
            if ruta_destino.exists():
                progress_bar.progress((i + 1) / total)
                continue
            
            try:
                response = self.session.get(url, stream=True)
                if "html" in response.headers.get("Content-Type", "") or response.status_code != 200:
                    st.warning(f"No disponible: {nombre_archivo}")
                else:
                    with open(ruta_destino, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
            except Exception as e:
                st.error(f"Error al descargar {nombre_archivo}: {e}")
            
            progress_bar.progress((i + 1) / total)

    def crear_carpeta_salida(self, estacion, fecha_texto):
        carpeta_salida = Path(f"data/{estacion}/{fecha_texto}")
        carpeta_salida.mkdir(parents=True, exist_ok=True)
        return carpeta_salida