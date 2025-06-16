import shutil
import subprocess
import gzip
import requests
import pandas as pd
from geopy.distance import geodesic
from zipfile import ZipFile
from pathlib import Path
from datetime import datetime, date
from tempfile import TemporaryDirectory
from IGS.generate_date import calculate_date, is_within_range
from IGS.authenticator import SessionWithHeaderRedirection
from IGS.sumary_checker import cargar_estaciones_tipo_S
from typing import Optional
import platform
import os



def load_df(path_archivo: str) -> pd.DataFrame:
    df = pd.read_csv(path_archivo, sep=",", header=0)
    df.columns = df.columns.str.strip().str.lower()
    df.rename(columns={
        "latitude": "latitud",
        "longitude": "longitud",
        "site name": "estacion"
    }, inplace=True)
    return df

def estaciones_mas_cercanas(latitud, longitud, df, top_n=2):
    ubicacion_usuario = (latitud, longitud)
    df["distancia_km"] = df.apply(
        lambda row: geodesic(ubicacion_usuario, (row["latitud"], row["longitud"])).kilometers,
        axis=1
    )
    df_ordenado = df.sort_values("distancia_km")
    return df_ordenado.head(top_n)

def obtener_vinculos(anio: int, doy: str, sitename: str, hora_inicio: int = 0, hora_fin: int = 23, rinex_version="3"):
    from IGS.sumary_checker import cargar_estaciones_tipo_S
    estaciones_tipo_S = cargar_estaciones_tipo_S()  # Se ejecuta solo cuando se llama esta función

    urls = []
    estacion_corto = sitename[:4].lower()
    yy = str(anio)[2:]
    tipo_archivo = "S" if rinex_version == "3" and estacion_corto in estaciones_tipo_S else "R"

    for hora in range(hora_inicio, hora_fin):
        for minuto in range(0, 60, 15):
            minuto=f"{minuto:02d}"
            if rinex_version == "2":
                letra_hora = chr(ord('a') + hora)
                nombre_archivo = f"{estacion_corto}{doy}{letra_hora}{minuto}.{yy}d.gz"
                url=(f"https://cddis.nasa.gov/archive/gnss/data/highrate/"f"{anio}/{doy}/{yy}d/{hora:02d}/{nombre_archivo}")
            else:
                nombre_archivo = f"{sitename}_{tipo_archivo}_{anio}{doy}{hora:02d}{minuto}_15M_01S_MO.crx.gz"
            
            url = (f"https://cddis.nasa.gov/archive/gnss/data/highrate/"
                f"{anio}/{doy}/{yy}d/{hora:02d}/{nombre_archivo}")
            urls.append((url, nombre_archivo))
    return urls

# insertar funcion de ruta ejecutable


def obtener_ruta_ejecutable(directorio_base: str = "data") -> Optional[Path]:
    sistema = platform.system().lower()
    nombre_ejecutable = "CRX2RNX.exe" if sistema == "windows" else "CRX2RNX"
    ruta = Path(directorio_base) / nombre_ejecutable

    if not ruta.exists():
        print(f"No se encontró '{nombre_ejecutable}' en la carpeta '{directorio_base}'.")
        return None

    if sistema != "windows" and not os.access(ruta, os.X_OK):
        try:
            os.chmod(ruta, 0o755)
        except Exception as e:
            print(f"Error al asignar permisos de ejecución a '{ruta}': {e}")
            return None

    return ruta


# ---  descomprimir_crx_gz  ---
def descomprimir_crx_gz(ruta_archivo_gz):
    ruta_crx = ruta_archivo_gz.with_suffix("")
    if ruta_crx.exists():
        ruta_crx.unlink()
    try:
        with gzip.open(ruta_archivo_gz, 'rb') as f_in:
            with open(ruta_crx, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return ruta_crx
    except Exception as e:
        print(f"Error al descomprimir {ruta_archivo_gz.name}: {e}")
        return None

# modificar convertir_a_rnx para que reciba la ruta ---
def convertir_a_rnx(ruta_crx: Path, ruta_ejecutable: Path, rinex_version="3"):

    try:
        # Lógica para determinar el nombre de salida
        if rinex_version == "2":
            yy = ruta_crx.name.split('.')[-1][0:2]
            ruta_convertida = ruta_crx.with_suffix(f".{yy}o")
        else:
            ruta_convertida = ruta_crx.with_suffix(".rnx")

        if ruta_convertida.exists():
            ruta_convertida.unlink()

        comando = [str(ruta_ejecutable), "-f", str(ruta_crx)] # setear ruta

        result = subprocess.run(
            comando,
            cwd=str(Path(__file__).parent.parent),  # asegura que cwd sea /app  / # ruta_crx.parent,
            capture_output=True,
            text=True,
            shell=False,
            check=False
        )
        if result.returncode == 0:
            if ruta_convertida.exists():
                return ruta_convertida
            else:
                print(f"CRX2RNX ejecutado, pero no se encontró: {ruta_convertida.name}")
        else:
            print(f"Error en CRX2RNX ({ruta_crx.name}):\n{result.stderr}")
    except Exception as e:
        print(f"Excepción al ejecutar CRX2RNX: {e}")
    return None 

# añadir funcion
def download_file_zip(fecha, estacion, hora_inicio=0, hora_fin=24, rinex_version="3"):
    ruta_exe = obtener_ruta_ejecutable() #obtener la ruta del ejecutable AL PRINCIPIO.
    if not ruta_exe:
        return False, "Proceso fallido: El ejecutable CRX2RNX.exe no fue encontrado.", None, None

    en_rango, dias_diff = is_within_range(fecha)
    if not en_rango:
        return False, f"⚠️ La fecha tiene {dias_diff} días de antigüedad (máx 182).", None, None

    anio, mes, dia = fecha.year, fecha.month, fecha.day
    doy = str(calculate_date(anio, mes, dia)).zfill(3)

    session = SessionWithHeaderRedirection()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    vinculos = obtener_vinculos(anio, doy, estacion, hora_inicio, hora_fin, rinex_version)

    temp_dir = TemporaryDirectory()
    carpeta_salida = Path(temp_dir.name)

    archivos_rnx = []
    print(f"\nIniciando descarga para la estación {estacion}...")
    
    for url, archivo in vinculos:
        ruta_gz = carpeta_salida / archivo
        try:
            r = session.get(url, stream=True, timeout=30)
            if r.status_code != 200:
                print(f"-> Fallo en URL (Status {r.status_code}): {url}")
                continue

            with open(ruta_gz, "wb") as f:
                f.write(r.content)
            
            print(f"-> Descargado: {archivo}")
            
            ruta_crx = descomprimir_crx_gz(ruta_gz)
            if not ruta_crx:
                continue

            #  la ruta del ejecutable a la función de conversión.
            ruta_rnx = convertir_a_rnx(ruta_crx, ruta_exe, rinex_version)
            
            if ruta_rnx and ruta_rnx.exists():
                archivos_rnx.append(ruta_rnx)
                if ruta_crx.exists(): ruta_crx.unlink()
            
            if ruta_gz.exists(): ruta_gz.unlink()

        except Exception as e:
            print(f"Error inesperado procesando {archivo}: {e}")

    if not archivos_rnx:
        temp_dir.cleanup()
        return False, "No se pudo descargar o convertir ningún archivo.", None, None

    zip_path = carpeta_salida / f"{estacion}_{fecha.strftime('%Y%m%d')}.zip"
    with ZipFile(zip_path, "w") as zipf:
        for archivo_rnx in archivos_rnx:
            zipf.write(archivo_rnx, arcname=archivo_rnx.name)

    return True, f"Archivos descargados y convertidos ({len(archivos_rnx)}).", zip_path, temp_dir






