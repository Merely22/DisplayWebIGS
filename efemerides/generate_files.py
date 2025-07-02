import gzip
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from IGS.authenticator import SessionWithHeaderRedirection

def construir_url_sp3(semana_gps, centro, tipo, producto, year, doy, muestreo="05M", duracion="01D", hora=0, minuto=0):
    ddd = f"{doy:03d}"
    hh = f"{hora:02d}"
    mm = f"{minuto:02d}"
    nombre_archivo = f"{centro}0{tipo}{producto}_{year}{ddd}{hh}{mm}_{duracion}_{muestreo}_ORB.SP3.gz"
    url = f"https://cddis.nasa.gov/archive/gnss/products/{semana_gps}/{nombre_archivo}"
    return url, nombre_archivo
def descargar_y_descomprimir_sp3(url, nombre_archivo, carpeta_final="descargas"):
    try:
        carpeta_destino = Path(carpeta_final)
        carpeta_destino.mkdir(exist_ok=True)

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            gz_path = temp_path / nombre_archivo
            sp3_path = carpeta_destino / nombre_archivo.replace(".gz", "")

            # Crear sesión autenticada con Earthdata
            session = SessionWithHeaderRedirection()
            session.headers.update({"User-Agent": "Mozilla/5.0"})

            response = session.get(url, stream=True, timeout=30)

            if response.status_code == 200:
                with open(gz_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Descomprimir el archivo .gz a .SP3
                with gzip.open(gz_path, "rb") as f_in, open(sp3_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

                return sp3_path

            elif response.status_code == 401:
                print("⚠️ Wrong (401). Verify your credential.")
            elif response.status_code == 404:
                print(f"⚠️ Not found: {url}")
            else:
                print(f"⚠️ HTTP error {response.status_code}: {response.reason}")

    except Exception as e:
        print(f"❌ General error: {e}")

    return None
