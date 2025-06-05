import time
import shutil
import subprocess
import gzip
from zipfile import ZipFile
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory
from IGS.generate_date import calculate_date, is_within_range
from IGS.authenticator import SessionWithHeaderRedirection
from IGS.sumary_checker import cargar_estaciones_tipo_S
import pandas as pd
from geopy.distance import geodesic
import requests

## CORRECCIÓN 1: Ruta al ejecutable con verificación
RUTA_CRX2RNX = Path("data/CRX2RNX.exe") # Usar "./CRX2RNX" en Linux
estaciones_tipo_S = cargar_estaciones_tipo_S()

# Carga de datos de estaciones
data_path = "data/igs_stations.csv"
df = pd.read_csv(data_path, sep=",", header=0)
df.columns = df.columns.str.strip().str.lower()
df.rename(columns={"latitude": "latitud", "longitude": "longitud", "site name": "estacion"}, inplace=True)

def estaciones_mas_cercanas(latitud, longitud, df, top_n=2):
    ubicacion_usuario = (latitud, longitud)
    df["distancia_km"] = df.apply(
        lambda row: geodesic(ubicacion_usuario, (row["latitud"], row["longitud"])).kilometers,
        axis=1
    )
    df_ordenado = df.sort_values("distancia_km")
    return df_ordenado.head(top_n)

def obtener_vinculos(anio: int, doy: str, sitename: str, hora_inicio: int = 0, hora_fin: int = 23, rinex_version="3"):
    urls = []
    estacion_corto = sitename[:4].lower()
    tipo_archivo = "S" if rinex_version == "3" and estacion_corto in estaciones_tipo_S else "R"

    for hora in range(hora_inicio, hora_fin):
        for minuto in range(0, 60, 15):
            if rinex_version == "2":
                nombre_archivo = f"{estacion_corto}_R_{anio}{doy}{hora:02d}{minuto:02d}_15M_01S_MO.crx.gz"
            else:
                nombre_archivo = f"{estacion_corto}_{tipo_archivo}_{anio}{doy}{hora:02d}{minuto:02d}_15M_01S_MO.crx.gz"
            
            url = (f"https://cddis.nasa.gov/archive/gnss/data/highrate/"
                f"{anio}/{doy}/25d/{hora:02d}/{nombre_archivo}")
            urls.append((url, nombre_archivo))

    return urls

def descomprimir_crx_gz(ruta_archivo_gz):
    ruta_crx = ruta_archivo_gz.with_suffix("")
    if ruta_crx.exists():
        ruta_crx.unlink() # Borra el archivo .crx si ya existe para evitar problemas
    try:
        with gzip.open(ruta_archivo_gz, 'rb') as f_in:
            with open(ruta_crx, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return ruta_crx
    except Exception as e:
        print(f"Error al descomprimir {ruta_archivo_gz.name}: {e}")
        return None

def convertir_a_rnx(ruta_crx: Path):
    try:
        ruta_rnx = ruta_crx.with_suffix(".rnx")
        if ruta_rnx.exists():
            ruta_rnx.unlink()

        result = subprocess.run(
            [str(RUTA_CRX2RNX), "-f", str(ruta_crx)],
            cwd=ruta_crx.parent,
            capture_output=True,
            text=True,
            shell=False,
            check=False # Para que no lance excepción si falla, y podamos leer el error
        )
        if result.returncode == 0:
            # A veces CRX2RNX no renombra el archivo y lo deja como .YYo, hay que renombrarlo
            archivo_obs = ruta_crx.with_suffix(f".{str(ruta_crx.name.split('_')[2][:2])}o")
            if archivo_obs.exists():
                archivo_obs.rename(ruta_rnx)
                
            if ruta_rnx.exists():
                print(f"Convertido exitosamente: {ruta_crx.name} -> {ruta_rnx.name}")
                return ruta_rnx
            else:
                print(f"❌ Error: El archivo convertido {ruta_rnx.name} no se encontró después de la conversión.")
        else:
            print(f"❌ Error de conversión para {ruta_crx.name}:\n{result.stderr}")
    except Exception as e:
        print(f"❌ Fallo en ejecución de CRX2RNX: {e}")
    return None

def download_file_zip(fecha, estacion, hora_inicio=0, hora_fin=24, rinex_version="3"):
    en_rango, dias_diff = is_within_range(fecha)
    if not en_rango:
        return False, f"⚠️ Solo se permiten fechas hasta 182 días antes. Su fecha tiene {dias_diff} días.", None, None

    anio, mes, dia = fecha.year, fecha.month, fecha.day
    doy = str(calculate_date(anio, mes, dia)).zfill(3)

    session = SessionWithHeaderRedirection()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    vinculos = obtener_vinculos(anio, doy, estacion, hora_inicio, hora_fin, rinex_version)

    temp_dir = TemporaryDirectory()
    carpeta_salida = Path(temp_dir.name) / f"{estacion}_{fecha.strftime('%Y%m%d')}"
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    archivos_rnx = []
    urls_intentadas = 0
    urls_exitosas = 0

    print(f"\nIniciando descarga para la estación {estacion} en la fecha {fecha.date()}...")
    
    for url, archivo in vinculos:
        urls_intentadas += 1
        ruta_gz = carpeta_salida / archivo
        try:
            r = session.get(url, stream=True, timeout=30)
            
            ## CORRECCIÓN 3: Mejorar la depuración (debug) para ver por qué falla una URL
            if r.status_code != 200:
                print(f"-> Fallo en URL (Status {r.status_code}): {url}")
                continue # Pasa a la siguiente URL
                
            if "html" in r.headers.get("Content-Type", ""):
                print(f"-> Fallo en URL (recibido HTML, posible pág de error): {url}")
                continue

            with open(ruta_gz, "wb") as f:
                f.write(r.content)
            
            print(f"-> Descargado: {archivo}")
            urls_exitosas += 1

            # Paso 1: Descomprimir .gz -> .crx
            ruta_crx = descomprimir_crx_gz(ruta_gz)
            if not ruta_crx:
                continue

            # Paso 2: Convertir .crx -> .rnx
            ruta_rnx = convertir_a_rnx(ruta_crx)
            if ruta_rnx and ruta_rnx.exists():
                archivos_rnx.append(ruta_rnx)
                ruta_crx.unlink() # Borrar .crx intermedio
            
            ruta_gz.unlink() # Borrar .gz descargado

        except requests.exceptions.RequestException as e:
            print(f"Error de red al descargar {archivo}: {e}")
        except Exception as e:
            print(f"Error inesperado procesando {archivo}: {e}")

    print(f"Resumen de descarga: {urls_exitosas}/{urls_intentadas} URLs exitosas.")

    if not archivos_rnx:
        temp_dir.cleanup()
        return False, "No se pudo descargar o convertir ningún archivo. Revisa la consola para ver los errores de URL.", None, None

    zip_path = carpeta_salida.parent / f"{carpeta_salida.name}.zip"
    with ZipFile(zip_path, "w") as zipf:
        for archivo_rnx in archivos_rnx:
            zipf.write(archivo_rnx, arcname=archivo_rnx.name)

    return True, f"Archivos descargados y convertidos exitosamente ({len(archivos_rnx)} archivos).", zip_path, temp_dir