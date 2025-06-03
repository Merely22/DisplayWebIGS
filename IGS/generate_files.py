import time
import shutil
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile
from tempfile import TemporaryDirectory
from IGS.generate_date import calculate_date, is_within_range 
from IGS.authenticator import SessionWithHeaderRedirection
from geopy.distance import geodesic
import pandas as pd

# Load station data
data_path = "data/igs_stations.csv"
df = pd.read_csv(data_path, sep=",", header=0)
df.columns = df.columns.str.strip().str.lower()
df.rename(columns={"Latitude": "latitud", "Longitude": "longitud", "Site Name": "estacion"}, inplace=True)

def estaciones_mas_cercanas(latitud, longitud, df, top_n=2):
    ubicacion_usuario = (latitud, longitud)
    df["distancia_km"] = df.apply(
        lambda row: geodesic(ubicacion_usuario, (row["latitud"], row["longitud"])).kilometers,
        axis=1
    )
    df_ordenado = df.sort_values("distancia_km")
    return df_ordenado.head(top_n)

def obtener_vinculos(anio: int, doy: str, estacion: str, hora_inicio: int = 0, hora_fin: int = 23) -> list:
    urls = []
    for hora in range(hora_inicio, hora_fin):
        for minuto in range(0, 60, 15):
            nombre_archivo = f"{estacion}_R_{anio}{doy}{hora:02d}{minuto:02d}_15M_01S_MO.crx.gz"
            url = (f"https://cddis.nasa.gov/archive/gnss/data/highrate/"
                   f"{anio}/{doy}/25d/{hora:02d}/{nombre_archivo}")
            urls.append((url, nombre_archivo))
    return urls

def download_file_zip(fecha: datetime, estacion: str, hora_inicio: int = 0, hora_fin: int = 23) -> tuple:

    en_rango, dias_diff = is_within_range(fecha)
    if not en_rango:
        return False, f"⚠️ Solo se permiten fechas hasta 182 días antes. Su fecha tiene {dias_diff} días.", None, None

    anio, mes, dia = fecha.year, fecha.month, fecha.day
    doy = str(calculate_date(anio, mes, dia)).zfill(3)

    session = SessionWithHeaderRedirection()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    vinculos = obtener_vinculos(anio, doy, estacion, hora_inicio, hora_fin)

    temp_dir = TemporaryDirectory()
    carpeta_salida = Path(temp_dir.name) / f"{estacion}_{fecha.strftime('%Y%m%d')}"
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    archivos_descargados = 0

    for url, archivo in vinculos:
        destino = carpeta_salida / archivo
        try:
            r = session.get(url, stream=True, timeout=30)
            if "html" in r.headers.get("Content-Type", "") or r.status_code != 200:
                continue
            with open(destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            archivos_descargados += 1
            time.sleep(1.5)
        except Exception:
            continue  # Puedes agregar logging.warning si quieres

    if archivos_descargados == 0:
        temp_dir.cleanup()
        return False, "⚠️ No se pudo descargar ningún archivo.", None, None

    zip_path = Path(temp_dir.name) / f"{carpeta_salida.name}.zip"
    shutil.make_archive(str(zip_path).replace(".zip", ""), 'zip', root_dir=carpeta_salida)

    return True, "✅ Archivos descargados y comprimidos", zip_path, temp_dir