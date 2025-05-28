import os
from zipfile import ZipFile
from pathlib import Path
from datetime import datetime
from shutil import make_archive
from src.generate_date import calculate_date, is_within_range
from src.authenticator import SessionWithHeaderRedirection

def obtener_vinculos(anio, doy, estacion):
    urls = []
    for hora in range(24):
        for minuto in range(0, 60, 15):
            nombre_archivo = f"{estacion}_R_{anio}{doy}{hora:02d}{minuto:02d}_15M_01S_MO.crx.gz"
            url = (f"https://cddis.nasa.gov/archive/gnss/data/highrate/"
                   f"{anio}/{doy}/25d/{hora:02d}/{nombre_archivo}")
            urls.append((url, nombre_archivo))
    return urls

def download_file_zip(fecha, estacion):
    hoy = datetime.today()
    en_rango, dias_diff = is_within_range(fecha)
    if not en_rango:
        return False, f"⚠️ Solo se permiten fechas hasta 182 días antes. Su fecha tiene {dias_diff} días.", None

    anio, mes, dia = fecha.year, fecha.month, fecha.day
    doy = str(calculate_date(anio, mes, dia)).zfill(3)
    carpeta_salida = Path(f"temp_data/{estacion}/{fecha.strftime('%Y-%m-%d')}")
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    session = SessionWithHeaderRedirection()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    vinculos = obtener_vinculos(anio, doy, estacion)

    archivos_descargados = 0

    for url, archivo in vinculos:
        destino = carpeta_salida / archivo
        if destino.exists():
            archivos_descargados += 1
            continue
        try:
            r = session.get(url, stream=True)
            if "html" in r.headers.get("Content-Type", "") or r.status_code != 200:
                continue
            with open(destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            archivos_descargados += 1
        except Exception as e:
            print(f"Error al descargar {archivo}: {e}")

    if archivos_descargados == 0:
        return False, "⚠️ No se pudo descargar ningún archivo.", None

    # Crear archivo zip
    zip_path = carpeta_salida.parent / f"{fecha.strftime('%Y-%m-%d')}.zip"
    make_archive(str(zip_path).replace(".zip", ""), 'zip', root_dir=carpeta_salida)

    return True, "✅ Archivos descargados y comprimidos correctamente.", str(zip_path)
