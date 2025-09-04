import shutil
import subprocess
import gzip
import requests
import pandas as pd
import re
import os
from geopy.distance import geodesic
from zipfile import ZipFile
from pathlib import Path
from datetime import datetime, date
from tempfile import TemporaryDirectory
from IGS.generate_date import calculate_date, is_within_range
from IGS.authenticator import SessionWithHeaderRedirection
from IGS.sumary_checker import cargar_estaciones_tipo_S
from typing import Optional

estaciones_tipo_S = cargar_estaciones_tipo_S()

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
    urls = []
    estacion_corto = sitename[:4].lower()
    yy = str(anio)[2:]
    tipo_archivo = "S" if rinex_version == "3" and sitename in estaciones_tipo_S else "R"

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
    ruta = Path(directorio_base) / "CRX2RNX.exe"
    if not ruta.exists():
        print(f"No se encontró 'CRX2RNX.exe' en la carpeta '{directorio_base}'.")
        return None
    return ruta

def localizar_gfzrnx(directorio_base: str = "data", ruta_config: Optional[str] = None) -> Optional[Path]:
    def ok(p: Path) -> bool:
        return p.exists() and p.is_file() and os.access(str(p), os.X_OK)
    if ruta_config:
        p = Path(ruta_config).resolve()
        if ok(p): return p
    env_path = os.getenv("GFZRNX_PATH")
    if env_path:
        p = Path(env_path).resolve()
        if ok(p): return p
    for d in (Path(directorio_base), Path(directorio_base) / "bin"):
        for name in ("gfzrnx.exe", "gfzrnx"):
            p = (d / name).resolve()
            if ok(p): return p
    for name in ("gfzrnx.exe", "gfzrnx"):
        found = shutil.which(name)
        if found:
            p = Path(found).resolve()
            if ok(p): return p
    print("No se encontró 'gfzrnx'.")
    return None

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
            cwd=ruta_crx.parent,
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

# unir archivos descargados con gfzrnx
# --- helpers de nombre (v3 y v2) ---
def _nombre_merge_desde_primero_v3(first_path: Path, horas_total: int, ext_out: str = "rnx") -> str:
    name = first_path.name
    m = re.match(
        r'^(?P<site>[A-Za-z0-9]+)_(?P<tipo>[SR])_(?P<anio>\d{4})(?P<doy>\d{3})(?P<hh>\d{2})(?P<mm>\d{2})_(?P<intv>[^_]+)_(?P<rest>.+?)\.(?P<ext>rnx|obs|crx)$',
        name
    )
    if m:
        g = m.groupdict()
        return f"{g['site']}_{g['tipo']}_{g['anio']}{g['doy']}{g['hh']}{g['mm']}_{horas_total:02d}H_{g['rest']}.{ext_out}"
    return f"{first_path.stem}_MERGED_{horas_total:02d}H.{ext_out}"
def _nombre_merge_desde_primero_v2(first_path: Path, horas_total: int) -> str:
    name = first_path.name
    m = re.match(
        r'^(?P<site>[A-Za-z0-9]{4})(?P<doy>\d{3})(?P<hour>[a-zA-Z])(?P<mm>\d{2})\.(?P<yy>\d{2})o$',
        name
    )
    if m:
        g = m.groupdict()
        return f"{g['site']}{g['doy']}{g['hour']}{g['mm']}_{horas_total:02d}H.{g['yy']}o"
    return f"{first_path.stem}_MERGED_{horas_total:02d}H{first_path.suffix}"

def unir_archivos_rnx(archivos_rnx: list[Path],
                      rinex_version: str,
                      horas_total: int,
                      ruta_gfzrnx: Optional[Path] = None) -> Optional[Path]:
    if not archivos_rnx:
        print("unir_archivos_rnx: lista vacía.")
        return None
    archivos_rnx = sorted(archivos_rnx, key=lambda p: p.name)
    first = archivos_rnx[0]
    if rinex_version == "2":
        out_name = _nombre_merge_desde_primero_v2(first, horas_total)
        vo = "2.11"
    else:
        out_name = _nombre_merge_desde_primero_v3(first, horas_total, ext_out="rnx")
        vo = "3.04"
    out_path = first.parent / out_name
    gfz = ruta_gfzrnx or localizar_gfzrnx()
    if not gfz:
        print("GFZRNX no disponible; no se puede fusionar.")
        return None
    cmd = [str(gfz),
           "-finp", *[str(p) for p in archivos_rnx],
           "-fout", str(out_path),
           "-splice_memsave", "-try_append", "900",
           "-vo", vo]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"GFZRNX merge falló:\nCMD: {' '.join(cmd)}\nSTDERR:\n{proc.stderr}")
        return None
    if not out_path.exists():
        print(f"GFZRNX no generó el archivo esperado: {out_path}")
        return None
    return out_path
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

            # convertir .crx/.d -> .rnx o .{yy}o
            ruta_rnx = convertir_a_rnx(ruta_crx, ruta_exe, rinex_version)

            if ruta_rnx and ruta_rnx.exists():
                archivos_rnx.append(ruta_rnx)
                if ruta_crx.exists():
                    ruta_crx.unlink()

            if ruta_gz.exists():
                ruta_gz.unlink()

        except Exception as e:
            print(f"Error inesperado procesando {archivo}: {e}")

    if not archivos_rnx:
        temp_dir.cleanup()
        return False, "No se pudo descargar o convertir ningún archivo.", None, None

    try:
        horas_total = int(hora_fin) - int(hora_inicio)
    except Exception:
        horas_total = hora_fin - hora_inicio

    if horas_total <= 0:
        temp_dir.cleanup()
        return False, "La ventana seleccionada es inválida (hora_fin debe ser mayor a hora_inicio).", None, None

    # === intentar MERGE con GFZRNX (compat. v2/v3) ===
    merged_path = unir_archivos_rnx(
        archivos_rnx=archivos_rnx,
        rinex_version=rinex_version,
        horas_total=horas_total,
        ruta_gfzrnx=None
    )

    # === crear ZIP: si merge ok -> solo merged; si no -> fragmentos ===
    zip_path = carpeta_salida / f"{estacion}_{fecha.strftime('%Y%m%d')}.zip"
    with ZipFile(zip_path, "w") as zipf:
        if merged_path and merged_path.exists():
            zipf.write(merged_path, arcname=merged_path.name)
            msg = f"Saved → {merged_path.name}."
        else:
            for archivo_rnx in archivos_rnx:
                zipf.write(archivo_rnx, arcname=archivo_rnx.name)
            msg = f"No se pudo fusionar."

    return True, msg, zip_path, temp_dir

def obtener_rnx_para_estacion(fecha, estacion, hora_inicio=0, hora_fin=24, rinex_version="3"):
    ruta_exe = obtener_ruta_ejecutable()
    if not ruta_exe:
        return False, "No se encontró CRX2RNX.exe.", [], None
    en_rango, dias_diff = is_within_range(fecha)
    if not en_rango:
        return False, f"⚠️ La fecha tiene {dias_diff} días de antigüedad (máx 182).", [], None
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
                for chunk in r.iter_content(chunk_size=1<<20):
                    if chunk:
                        f.write(chunk)

            print(f"-> Descargado: {archivo}")

            ruta_crx = descomprimir_crx_gz(ruta_gz)
            if not ruta_crx:
                continue

            ruta_rnx = convertir_a_rnx(ruta_crx, ruta_exe, rinex_version)
            if ruta_rnx and ruta_rnx.exists():
                archivos_rnx.append(ruta_rnx)
                if ruta_crx.exists(): ruta_crx.unlink()

            if ruta_gz.exists(): ruta_gz.unlink()

        except Exception as e:
            print(f"Error inesperado procesando {archivo}: {e}")

    if not archivos_rnx:
        temp_dir.cleanup()
        return False, "No se pudo descargar o convertir ningún archivo.", [], None

    # ventana en horas (fin exclusivo)
    try:
        horas_total = int(hora_fin) - int(hora_inicio)
    except Exception:
        horas_total = hora_fin - hora_inicio
    if horas_total <= 0:
        temp_dir.cleanup()
        return False, "Ventana inválida (hora_fin > hora_inicio).", [], None

    # intentar MERGE con GFZRNX
    merged_path = unir_archivos_rnx(
        archivos_rnx=archivos_rnx,
        rinex_version=rinex_version,
        horas_total=horas_total,
        ruta_gfzrnx=None
    )
    if merged_path and merged_path.exists():
        return True, f"Merged OK → {merged_path.name}", [merged_path], temp_dir
    else:
        return True, f"No se pudo fusionar; se devuelven {len(archivos_rnx)} fragmentos.", archivos_rnx, temp_dir



