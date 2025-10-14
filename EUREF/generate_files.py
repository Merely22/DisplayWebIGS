from __future__ import annotations
import io
import os
import re
import gzip
import shutil
import zipfile
import requests
import subprocess
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd
from geopy.distance import geodesic

BKG_BASES = {
    "IGS":   "https://igs.bkg.bund.de/root_ftp/IGS/highrate/{year}/{doy}/{hour_letter}/{filename}",
    "EUREF": "https://igs.bkg.bund.de/root_ftp/EUREF/highrate/{year}/{doy}/{hour_letter}/{filename}",
}

MINUTOS_15M = (0, 15, 30, 45)

@dataclass
class HighRateLink:
    url: str
    filename: str
    hour: int
    minute: int
    tipo: str     # 'S' o 'R'
    carpeta: str  # 'IGS' o 'EUREF'


# ------------------ helpers carpeta ------------------

def _normalize_carpeta_value(value: Optional[str]) -> str:
    if not value:
        return "IGS"
    v = str(value).strip().upper()
    if v == "IGS":
        return "IGS"
    if v in {"EPN", "EUREF"}:
        return "EUREF"
    # fallback
    return "IGS"

def _build_url(year: int, doy: Union[int, str], hora: int, filename: str, carpeta: str) -> str:
    d3 = f"{int(doy):03d}"
    letter = chr(ord('a') + hora)  # 0->a ... 23->x
    repo = _normalize_carpeta_value(carpeta)
    base = BKG_BASES.get(repo, BKG_BASES["IGS"])
    return base.format(year=year, doy=d3, hour_letter=letter, filename=filename)


# ------------------ S/R helpers ------------------

def _tipos_auto(site: str, estaciones_tipo_S: Optional[Iterable[str]]) -> List[str]:
    """
    Si sabemos que la estación es 'S' -> ['S'], si no -> intentar ambos ['S','R'].
    """
    if estaciones_tipo_S:
        sset = {s.upper() for s in estaciones_tipo_S}
        if site.upper() in sset:
            return ["S"]
    return ["S", "R"]


def build_filename(station: str, tipo: str, anio: int, doy: Union[int, str], hora: int, minuto: int,
                   cadencia: str = "15M", muestreo: str = "01S", sufijo: str = "MO.crx.gz") -> str:
    station = station.upper().strip().rstrip("_")
    d3 = f"{int(doy):03d}"
    return f"{station}_{tipo}_{anio}{d3}{hora:02d}{minuto:02d}_{cadencia}_{muestreo}_{sufijo}"


# =========================================================
# CSV: cargar, detectar columnas, mantener 'carpeta'
# =========================================================

def _detect_station_col(df: pd.DataFrame) -> str:
    best, hits = None, -1
    for c in df.columns:
        if df[c].dtype == object:
            n = df[c].astype(str).str.upper().str.strip().str.fullmatch(r"[A-Z0-9]{9}").sum()
            if n > hits:
                best, hits = c, int(n)
    if best is None or hits == 0:
        for c in df.columns:
            if df[c].dtype == object and df[c].astype(str).str.contains(r"[A-Z0-9]{9}", regex=True).any():
                return c
        raise ValueError("No se pudo detectar la columna de estación (9 caracteres).")
    return best

def _detect_lat_lon_cols(df: pd.DataFrame) -> Tuple[str, str]:
    m = {c.lower(): c for c in df.columns}
    lat = m.get("latitude") or m.get("lat")
    lon = m.get("longitude") or m.get("lon")
    if not lat or not lon:
        raise ValueError("Faltan columnas Latitude/Longitude.")
    return lat, lon

def _detect_carpeta_col(df: pd.DataFrame) -> Optional[str]:
    # admite 'carpeta', 'folder', 'repo'
    m = {c.lower(): c for c in df.columns}
    return m.get("carpeta") or m.get("folder") or m.get("repo")

def cargar_estaciones_local(ruta_csv: Union[str, os.PathLike]) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv)
    station_col = _detect_station_col(df)
    lat_col, lon_col = _detect_lat_lon_cols(df)
    carpeta_col = _detect_carpeta_col(df)

    df = df.rename(columns={station_col: "station", lat_col: "latitude", lon_col: "longitude"})
    if carpeta_col:
        df = df.rename(columns={carpeta_col: "carpeta"})

    df["station"]   = df["station"].astype(str).str.upper().str.extract(r"([A-Z0-9]{9})", expand=False)
    df["latitude"]  = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    if "carpeta" in df.columns:
        df["carpeta"] = df["carpeta"].map(_normalize_carpeta_value)
    else:
        df["carpeta"] = "IGS"

    df = df.dropna(subset=["station", "latitude", "longitude"]).reset_index(drop=True)
    return df

def cargar_estaciones_tipo_S(ruta_csv: Union[str, os.PathLike]) -> set[str]:
    """
    Si el CSV trae columna 'Tipo' y una columna de estación, devuelve set de estaciones con 'S'.
    """
    df = pd.read_csv(ruta_csv)
    cols = {c.lower(): c for c in df.columns}
    col_station = cols.get("station") or cols.get("estación") or cols.get("estacion") or cols.get("site name") or cols.get("name")
    col_tipo = cols.get("tipo")
    if not col_station or not col_tipo:
        raise ValueError("CSV sin columnas 'Tipo' + 'Station/Estación'.")
    s = set(
        df[df[col_tipo].astype(str).str.upper().str.contains("S", regex=False)][col_station]
        .astype(str).str.upper().str.extract(r"([A-Z0-9]{9})", expand=False)
        .dropna().tolist()
    )
    return s

def estaciones_mas_cercanas(df: pd.DataFrame, lat: float, lon: float, n: int = 4) -> pd.DataFrame:
    if not {"station", "latitude", "longitude"} <= set(df.columns):
        raise ValueError("El DataFrame debe tener 'station','latitude','longitude'.")
    p = (lat, lon)
    df = df.copy()
    df["distance_km"] = df.apply(lambda r: geodesic(p, (r["latitude"], r["longitude"])).kilometers, axis=1)
    # Mantiene 'carpeta' en el resultado
    return df.sort_values("distance_km").head(n).reset_index(drop=True)


# =========================================================
# Vínculos, descarga, CRX2RNX, GFZRNX
# =========================================================

def obtener_vinculos_igs_highrate(
    anio: int,
    doy: Union[int, str],
    sitename: str,
    hora_inicio: int,
    hora_fin: int,                   # EXCLUSIVO
    estaciones_tipo_S: Optional[Iterable[str]] = None,
    carpeta: str = "IGS",
    minutos: Sequence[int] = MINUTOS_15M,
) -> List[HighRateLink]:
    site = sitename.upper().strip().rstrip("_")
    tipos = _tipos_auto(site, estaciones_tipo_S)
    carpeta_norm = _normalize_carpeta_value(carpeta)

    out: List[HighRateLink] = []
    for hh in range(int(hora_inicio), int(hora_fin)):
        for mm in minutos:
            for t in tipos:
                fname = build_filename(site, t, anio, doy, hh, mm)
                url = _build_url(anio, doy, hh, fname, carpeta_norm)
                out.append(HighRateLink(url=url, filename=fname, hour=hh, minute=mm, tipo=t, carpeta=carpeta_norm))
    return out


# ---------- descompresión, conversión, merge ----------

def _descomprimir_crx_gz(ruta_gz: Path) -> Optional[Path]:
    dst = ruta_gz.with_suffix("")  # .crx.gz -> .crx
    if dst.exists():
        dst.unlink()
    try:
        with gzip.open(ruta_gz, "rb") as f_in, open(dst, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return dst
    except Exception:
        return None

def _obtener_crx2rnx(directorio_base: str = "data") -> Optional[Path]:
    p = Path(directorio_base) / "CRX2RNX.exe"
    if p.exists():
        return p.resolve()
    found = shutil.which("CRX2RNX") or shutil.which("crx2rnx")
    return Path(found).resolve() if found else None

def _convertir_a_rnx(ruta_crx: Path, ruta_crx2rnx: Path) -> Optional[Path]:
    out = ruta_crx.with_suffix(".rnx")
    if out.exists():
        out.unlink()
    cmd = [str(ruta_crx2rnx), "-f", str(ruta_crx)]
    try:
        res = subprocess.run(cmd, cwd=ruta_crx.parent, capture_output=True, text=True, shell=False, check=False)
        if res.returncode == 0 and out.exists():
            return out
        return None
    except Exception:
        return None

def _localizar_gfzrnx(directorio_base: str = "data", ruta_config: Optional[str] = None) -> Optional[Path]:
    def ok(p: Path) -> bool:
        return p.exists() and p.is_file() and os.access(str(p), os.X_OK)
    if ruta_config:
        p = Path(ruta_config).resolve()
        if ok(p): return p
    env = os.getenv("GFZRNX_PATH")
    if env:
        p = Path(env).resolve()
        if ok(p): return p
    for d in (Path(directorio_base), Path(directorio_base) / "bin"):
        for nm in ("gfzrnx.exe", "gfzrnx"):
            p = (d / nm).resolve()
            if ok(p): return p
    found = shutil.which("gfzrnx.exe") or shutil.which("gfzrnx")
    return Path(found).resolve() if found else None

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

def _unir_archivos_rnx(archivos_rnx: List[Path], horas_total: int, ruta_gfzrnx: Optional[Path] = None) -> Optional[Path]:
    if not archivos_rnx:
        return None
    archivos_rnx = sorted(archivos_rnx, key=lambda p: p.name)
    first = archivos_rnx[0]
    out = first.parent / _nombre_merge_desde_primero_v3(first, horas_total, "rnx")
    gfz = ruta_gfzrnx or _localizar_gfzrnx()
    if not gfz:
        return None
    cmd = [str(gfz), "-finp", *[str(p) for p in archivos_rnx], "-fout", str(out),
           "-splice_memsave", "-try_append", "900", "-vo", "3.04"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out.exists():
        return None
    return out

#    cmd = [str(gfz),
           #"-finp", *[str(p) for p in archivos_rnx],
           ##"-fout", str(out_path),
           #"-splice_memsave", "-try_append", "900",
           #"-vo", vo]
def descargar_y_procesar_estacion(
    station: str,
    anio: int,
    doy: Union[int, str],
    hora_inicio: int,
    hora_fin: int,
    estaciones_tipo_S: Optional[Iterable[str]] = None,
    carpeta: str = "IGS",
) -> Tuple[bool, str, io.BytesIO]:

    site = station.upper().strip().rstrip("_")
    links = obtener_vinculos_igs_highrate(
        anio=anio, doy=doy, sitename=site,
        hora_inicio=hora_inicio, hora_fin=hora_fin,
        estaciones_tipo_S=estaciones_tipo_S, carpeta=carpeta
    )

    ruta_crx2rnx = _obtener_crx2rnx()
    if not ruta_crx2rnx:
        return False, "CRX2RNX no encontrado (coloca CRX2RNX.exe en data/ o añade al PATH).", io.BytesIO()

    horas_total = int(hora_fin) - int(hora_inicio)
    if horas_total <= 0:
        return False, "Ventana horaria inválida (hora_fin > hora_inicio).", io.BytesIO()

    archivos_rnx: List[Path] = []
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        for lk in links:
            gz_path = tmp / lk.filename
            try:
                r = requests.get(lk.url, stream=True, timeout=30)
                if r.status_code not in (200, 206):
                    continue
                with open(gz_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        if chunk:
                            f.write(chunk)
                crx_path = _descomprimir_crx_gz(gz_path)
                if not crx_path:
                    continue
                rnx_path = _convertir_a_rnx(crx_path, ruta_crx2rnx)
                if rnx_path and rnx_path.exists():
                    archivos_rnx.append(rnx_path)
                try:
                    if crx_path.exists(): crx_path.unlink()
                    if gz_path.exists(): gz_path.unlink()
                except Exception:
                    pass
            except Exception:
                continue

        if not archivos_rnx:
            return False, f"{site} [{_normalize_carpeta_value(carpeta)}]: no se pudo descargar/convertir ningún archivo.", io.BytesIO()

        merged = _unir_archivos_rnx(archivos_rnx, horas_total=horas_total)
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            if merged and merged.exists():
                zf.write(merged, arcname=merged.name)
                msg = f"{site} [{_normalize_carpeta_value(carpeta)}]: merged OK → {merged.name}"
            else:
                for p in archivos_rnx:
                    zf.write(p, arcname=p.name)
                msg = f"{site} [{_normalize_carpeta_value(carpeta)}]: no se pudo fusionar; se incluyen {len(archivos_rnx)} fragmentos."
        zip_buf.seek(0)
        return True, msg, zip_buf


def combinar_zips_estaciones(zips_por_estacion: List[Tuple[str, io.BytesIO]]) -> io.BytesIO:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for station, buf in zips_por_estacion:
            try:
                with zipfile.ZipFile(buf, "r") as zin:
                    for info in zin.infolist():
                        data = zin.read(info.filename)
                        zout.writestr(f"{station}/{Path(info.filename).name}", data)
            except Exception:
                continue
    out.seek(0)
    return out
