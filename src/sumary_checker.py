import pandas as pd
from datetime import datetime
import requests
from io import StringIO
from src.authenticator import SessionWithHeaderRedirection
def descargar_summary(anio):
    base_url = "https://cddis.nasa.gov/archive/gnss/data/highrate/reports/"
    if anio == datetime.utcnow().year:
        url = f"{base_url}hrv23_summary.current"
    else:
        url = f"{base_url}hrv23_summary.{anio}"

    print(f"\n📥 Descargando summary desde: {url}")
    
    session = SessionWithHeaderRedirection()
    r = session.get(url, stream=True, timeout=30)

    if "html" in r.headers.get("Content-Type", ""):
        print("❌ Error: contenido HTML recibido. Posible error de autenticación.")
        raise Exception("Error de autenticación: no se pudo descargar el summary.")

    r.raise_for_status()
    texto = r.text
    print("🧾 Primeras líneas del summary:")
    print('\n'.join(texto.splitlines()[:10]))
    return texto
def parsear_summary(contenido_txt):
    from io import StringIO

    df = pd.read_fwf(
        StringIO(contenido_txt),
        skiprows=5,
        colspecs=[
            (2, 6),    # Site
            (8, 9),    # Version (RINEX)
            (11, 29),  # Description (no se usa pero útil para debug)
            (31, 38),  # Lat
            (40, 48),  # Lon
            (50, 61),  # Start
            (63, 68),  # StartDOY
            (70, 81),  # End
            (83, 88),  # EndDOY
        ],
        names=["Site", "Version", "Description", "Lat", "Lon", "Start", "StartDOY", "End", "EndDOY"]
    )

    df["Site"] = df["Site"].str.strip().str.upper()
    df["Version"] = df["Version"].astype(str).str.strip()
    df["Start"] = pd.to_datetime(df["Start"], errors="coerce", format="%d-%b-%y")
    df["End"] = pd.to_datetime(df["End"], errors="coerce", format="%d-%b-%y")

    summary_dict = {
        row["Site"]: {
            "Start": row["Start"],
            "End": row["End"],
            "Format": row["Version"]
        }
        for _, row in df.iterrows()
        if pd.notna(row["Start"]) and pd.notna(row["End"])
    }

    print(f"✅ Total estaciones parseadas: {len(summary_dict)}")
    return summary_dict
def verificar_disponibilidad_summary(sitename, fecha, summary_dict, csv_df):
    csv_df.columns = csv_df.columns.str.strip()
    nombre_corto = sitename[:4].upper()
    print(f"\n🔎 Verificando estación: {sitename} → código: {nombre_corto}")

    fila_csv = csv_df[csv_df["Site Name"].str.startswith(nombre_corto)]
    if fila_csv.empty:
        print("❌ No se encontró en el CSV local")
        return False, "La estación no está en el CSV local."

    tiene_rate1s = fila_csv["Rate 1s"].values[0].strip().upper() == "SI"
    print(f"✅ Tiene rate 1s: {tiene_rate1s}")
    if not tiene_rate1s:
        return False, "La estación no tiene datos en 1s (según CSV local)."

    if nombre_corto not in summary_dict:
        print("❌ No encontrada en summary_dict")
        print(f"📌 Claves disponibles (primeros 10): {list(summary_dict.keys())[:10]}")
        return False, "La estación no está listada en el archivo summary del año seleccionado."

    info = summary_dict[nombre_corto]
    print(f"📅 Fecha seleccionada: {fecha.date()}, rango: {info['Start'].date()} → {info['End'].date()}")

    if pd.isna(info["Start"]) or pd.isna(info["End"]):
        return False, "Fechas inválidas en archivo summary."

    if not (info["Start"] <= fecha <= info["End"]):
        return False, f"La fecha está fuera del rango válido ({info['Start'].date()} a {info['End'].date()})."

    return True, f"✅ Datos 1s disponibles. Formato: RINEX v{info['Format']}"


def obtener_formato_rinex(sitename, summary_dict):
    nombre_corto = sitename[:4].upper()
    info = summary_dict.get(nombre_corto)
    if not info:
        return None
    return str(info["Format"])