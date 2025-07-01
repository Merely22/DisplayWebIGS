import gzip
from IGS.authenticator import SessionWithHeaderRedirection

def obtener_vinculos(anio: int, doy: str, sitename: str, hora_inicio: int = 0, hora_fin: int = 23, rinex_version="3"):
    urls = []
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
def descomprimir_SP3_gz(ruta_archivo_gz):
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