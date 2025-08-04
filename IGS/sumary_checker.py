import pandas as pd
from datetime import timezone, datetime
import requests
from io import StringIO
from IGS.authenticator import SessionWithHeaderRedirection
from pathlib import Path
def cargar_estaciones_tipo_S(ruta_csv="data/stations_s.csv"):
    ruta = Path(ruta_csv)
    if not ruta.exists():
        print(f"Archivo no encontrado: {ruta_csv}")
        return set()
    try:
        df = pd.read_csv(ruta, header=None, names=["Estacion"])
        estaciones = set(df["Estacion"].astype(str).str.strip().str.upper())
        #print(f"Cargadas {len(estaciones)} estaciones tipo 'S'")
        return estaciones
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return set()
def descargar_summary(anio):
    base_url = "https://cddis.nasa.gov/archive/gnss/data/highrate/reports/"
    if anio == datetime.utcnow().year:
        url = f"{base_url}hrv23_summary.current"
    else:
        url = f"{base_url}hrv23_summary.{anio}"
    #print(f"\n Descargando summary desde: {url}") 
    session = SessionWithHeaderRedirection()
    r = session.get(url, stream=True, timeout=30)
    if "html" in r.headers.get("Content-Type", ""):
        print(" Error: contenido HTML recibido. Posible error de autenticación.")
        raise Exception("Error de autenticación: no se pudo descargar el summary.")
    r.raise_for_status()
    texto = r.text
    #print("🧾 Primeras líneas del summary:")
    #print('\n'.join(texto.splitlines()[:10]))
    return texto
def parsear_summary(contenido_txt):
    from io import StringIO

    df = pd.read_fwf(
        StringIO(contenido_txt),
        skiprows=5,
        colspecs=[
            (2, 6),    # Site
            (8, 11),   # Version
            (11, 29),  # Description
            (31, 38),  # Latitud
            (40, 48),  # Longittud
            (50, 61),  # Start
            (63, 68),  # StartDOY
            (70, 81),  # End
            (83, 88),  # EndDOY
        ],
        names=["Site", "Version", "Description", "Lat", "Lon", "Start", "StartDOY", "End", "EndDOY"]
    )

    df["Site"] = df["Site"].str.strip().str.upper()
    df["Version"] = df["Version"].astype(str).str.strip()
    df["Start"] = pd.to_datetime(df["Start"], errors="coerce", format="%d-%b-%y").dt.tz_localize(timezone.utc)
    df["End"] = pd.to_datetime(df["End"], errors="coerce", format="%d-%b-%y").dt.tz_localize(timezone.utc)

    summary_dict = {
        row["Site"]: {
            "Start": row["Start"],
            "End": row["End"],
            "Format": row["Version"]
        }
        for _, row in df.iterrows()
        if pd.notna(row["Start"]) and pd.notna(row["End"])
    }
    return summary_dict

def verificar_disponibilidad_summary(sitename, fecha, summary_dict, csv_df):
    csv_df.columns = csv_df.columns.str.strip()
    nombre_corto = sitename[:4].upper()
    fila_csv = csv_df[csv_df["estacion"].str.startswith(nombre_corto)]
    
    if fila_csv.empty:
        print("Not found in local CSV.")
        return False, "The station is not listed in the local CSV file."
    
    tiene_rate1s = fila_csv["rate 1s"].values[0].strip().upper() == "SI"
    print(f"Has 1s rate data: {tiene_rate1s}")
    
    if not tiene_rate1s:
        return False, "The station has no 1s data (according to the local CSV)."
    
    if nombre_corto not in summary_dict:
        print("Not found in summary_dict.")
        return False, "The station is not listed in the database for the selected year."
    
    info = summary_dict[nombre_corto]
    
    if pd.isna(info["Start"]) or pd.isna(info["End"]):
        return False, "Invalid date range."
    
    if not (info["Start"] <= fecha <= info["End"]):
        return False, f"The selected date is out of range for this station. It must be between {info['Start'].date()} and {info['End'].date()}."
    
    return True, f"1s data available. Format: RINEX v{info['Format']}"



def obtener_formato_rinex(sitename, summary_dict):
    nombre_corto = sitename[:4].upper()
    info = summary_dict.get(nombre_corto)
    if not info:
        return None 
    version = str(info["Format"]).strip()
    if version.startswith("2"):
        return "2"
    elif version.startswith("3"):
        return "3"
    else:
        return None