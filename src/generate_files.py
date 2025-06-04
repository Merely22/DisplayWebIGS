import os
import time
import shutil
import subprocess
import gzip
from zipfile import ZipFile
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory
from src.generate_date import calculate_date, is_within_range
from src.authenticator import SessionWithHeaderRedirection
from src.sumary_checker import cargar_estaciones_tipo_S

RUTA_CRX2RNX = Path("./CRX2RNX.exe")#usar "./CRX2RNX" en linux
estaciones_tipo_S = cargar_estaciones_tipo_S()

def obtener_vinculos(anio, doy, estacion, hora_inicio=0, hora_fin=24, rinex_version="3"):
    urls = []
    doy_str = str(doy).zfill(3)
    estacion_corto = estacion[:4].lower()
    yy = str(anio)[2:]
    tipo_archivo="S" if rinex_version=="3" and estacion in estaciones_tipo_S else "R"
    for hora in range(hora_inicio, hora_fin):
        for minuto in range(0, 60, 15):
            minuto_str = f"{minuto:02d}"         
            if rinex_version == "2":
                #(a=00h, b=01h, ..., x=23h)
                letra_hora = chr(ord('a') + hora)
                nombre_archivo = f"{estacion_corto}{doy_str}{letra_hora}{minuto_str}.{yy}d.gz"
                url = (f"https://cddis.nasa.gov/archive/gnss/data/highrate/"
                       f"{anio}/{doy_str}/25d/{hora:02d}/{nombre_archivo}")
            else:
                nombre_archivo = f"{estacion}_{tipo_archivo}_{anio}{doy_str}{hora:02d}{minuto_str}_15M_01S_MO.crx.gz"
                url = (f"https://cddis.nasa.gov/archive/gnss/data/highrate/"
                       f"{anio}/{doy_str}/25d/{hora:02d}/{nombre_archivo}")           
            urls.append((url, nombre_archivo))
    return urls
def descomprimir_crx_gz(ruta_archivo_gz):
    ruta_crx = ruta_archivo_gz.with_suffix("")
    if ruta_crx.exists():
        return ruta_crx
    try:
        with gzip.open(ruta_archivo_gz, 'rb') as f_in:
            with open(ruta_crx, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return ruta_crx
    except Exception as e:
        return None
def convertir_a_rnx(ruta_crx: Path):
    try:
        ruta_rnx = ruta_crx.with_suffix(".rnx")
        if ruta_rnx.exists():
            ruta_rnx.unlink()  # Elimina el .rnx si ya existe para evitar conflicto

        result = subprocess.run(
            [str(RUTA_CRX2RNX), "-f", str(ruta_crx)],
            cwd=ruta_crx.parent,
            capture_output=True,
            text=True,
            shell=False
        )
        if result.returncode == 0:
            print(f"Convertido exitosamente: {ruta_crx.name}")
            if ruta_rnx.exists():
                return ruta_rnx
            else:
                print(f"No se generó el archivo esperado: {ruta_rnx.name}")
        else:
            print(f"❌ Error de conversión:\n{result.stderr}")
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

    for url, archivo in vinculos:
        ruta_gz = carpeta_salida / archivo
        try:
            r = session.get(url, stream=True, timeout=30)
            if "html" in r.headers.get("Content-Type", "") or r.status_code != 200:                
                continue
            with open(ruta_gz, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            if not ruta_gz.exists():
                continue
            with open(ruta_gz, "rb") as fcheck:
                cabecera = fcheck.read(4)
                if not cabecera.startswith(b'\x1f\x8b'):
                    continue
            # Paso 1: descomprimir .gz → .crx
            ruta_crx = descomprimir_crx_gz(ruta_gz)
            ruta_rnx = convertir_a_rnx(ruta_crx)
            if ruta_rnx and ruta_rnx.exists():
                archivos_rnx.append(ruta_rnx)
            else:
                print(f"Conversión fallida o archivo .rnx no encontrado para: {ruta_crx.name}")
            time.sleep(1.5)
        except Exception as e:
            print(f"Error al descargar {archivo}: {e}")

    if not archivos_rnx:
        temp_dir.cleanup()
        return False, "No se pudo descargar o convertir ningún archivo.", None, None

    zip_path = carpeta_salida.parent / f"{carpeta_salida.name}.zip"
    with ZipFile(zip_path, "w") as zipf:
        for archivo_rnx in archivos_rnx:
            zipf.write(archivo_rnx, arcname=archivo_rnx.name)

    return True, f"Archivos descargados y convertidos exitosamente ({len(archivos_rnx)} archivos).", zip_path, temp_dir
