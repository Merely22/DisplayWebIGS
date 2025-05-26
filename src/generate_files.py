from io import BytesIO
from zipfile import ZipFile
from src.generate_date import calculate_date
from pathlib import Path

def obtener_vinculos(anio, file_date_format, estacion):
    urls = []
    for hora in range(24):
        subcarpeta = f"{hora:02d}"
        for minuto in range(0, 60, 15):
            h = f"{hora:02d}"
            m = f"{minuto:02d}"
            nombre_archivo = f"{estacion}_R_{anio}{file_date_format}{h}{m}_15M_01S_MO.crx.gz"
            url = f"https://cddis.nasa.gov/archive/gnss/data/highrate/{anio}/{file_date_format}/25d/{subcarpeta}/{nombre_archivo}"
            urls.append((url, nombre_archivo))
    return urls

def download_file_zip(anio, mes, dia, estacion, session, guardar_zip_local=False):
    file_date_format = calculate_date(anio, mes, dia)
    vinculos = obtener_vinculos(anio, file_date_format, estacion)

    zip_buffer = BytesIO()
    fecha_texto = f"{anio}-{mes:02d}-{dia:02d}"
    nombre_zip = f"{estacion}_{fecha_texto}.zip"
    archivos_agregados = 0

    with ZipFile(zip_buffer, 'w') as zipf:
        for url, nombre_archivo in vinculos:
            try:
                response = session.get(url, stream=True, timeout=10)
                content_type = response.headers.get("Content-Type", "")
                if response.status_code == 200 and "html" not in content_type.lower():
                    data = response.content
                    if data:
                        zipf.writestr(nombre_archivo, data)
                        archivos_agregados += 1
            except Exception as e:
                print(f"Error al descargar {nombre_archivo}: {e}")

    if archivos_agregados == 0:
        raise Exception("No se pudo descargar ningún archivo válido para esa fecha.")

    zip_buffer.seek(0)

    # ✅ Guardar ZIP local si se desea
    if guardar_zip_local:
        output_path = Path(nombre_zip)
        with open(output_path, "wb") as f:
            f.write(zip_buffer.getvalue())

    return zip_buffer, nombre_zip
