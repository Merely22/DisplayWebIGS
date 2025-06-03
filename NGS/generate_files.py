import pandas as pd
import requests
from geopy.distance import geodesic

def cargar_estaciones_local(ruta_csv="data/NOAACORSNetwork.csv"):
    df = pd.read_csv(ruta_csv, sep=",", encoding="utf-8-sig", on_bad_lines='warn')
    if 'x' in df.columns and 'y' in df.columns:
        df = df[df['x'].str.contains(",", na=False) & df['y'].str.contains(",", na=False)].copy()
        df['Longitude'] = df['x'].str.replace(",", ".", regex=False).astype(float)
        df['Latitude'] = df['y'].str.replace(",", ".", regex=False).astype(float)
    elif 'LATITUDE' in df.columns and 'LONGITUDE' in df.columns:
        df['Latitude'] = df['LATITUDE'].str.replace(",", ".", regex=False).astype(float)
        df['Longitude'] = df['LONGITUDE'].str.replace(",", ".", regex=False).astype(float)
    else:
        raise ValueError("No se encontraron columnas válidas de coordenadas.")
    return df

def estaciones_mas_cercanas(df, lat_usuario, lon_usuario, n=2):
    punto_usuario = (lat_usuario, lon_usuario)
    df['Distancia_km'] = df.apply(lambda row: geodesic(punto_usuario, (row['Latitude'], row['Longitude'])).kilometers, axis=1)
    return df.sort_values('Distancia_km').head(n).copy()

def generar_nombre_archivo(siteid, anio, doy, tipo='obs'):
    siteid = siteid.lower()
    yy = str(anio)[-2:]
    doy_str = str(doy).zfill(3)
    if tipo == 'obs':
        return f"{siteid}{doy_str}0.{yy}o.gz"
    elif tipo == 'crx':
        return f"{siteid}{doy_str}0.{yy}d.gz"
    else:
        raise ValueError("Tipo inválido: usa 'obs' o 'crx'.")

def verificar_disponibilidad_rinex(df_cercanas, anio, doy, tipo='obs'):
    doy_str = str(doy).zfill(3)
    url_lista = f"https://noaa-cors-pds.s3.amazonaws.com/rinex/{anio}/{doy_str}/{anio}.{doy_str}.files.list"
    try:
        r = requests.get(url_lista)
        r.raise_for_status()
        contenido = r.text
    except Exception as e:
        print(f"❌ Error al obtener lista de archivos: {e}")
        df_cercanas['Disponible'] = "ERROR"
        df_cercanas['URL'] = None
        return df_cercanas

    disponibles = []
    urls = []

    for _, row in df_cercanas.iterrows():
        siteid = row['SITEID'].lower()
        nombre_archivo = generar_nombre_archivo(siteid, anio, doy, tipo)
        if nombre_archivo in contenido:
            disponibles.append("SI")
            url = f"https://noaa-cors-pds.s3.amazonaws.com/rinex/{anio}/{doy_str}/{siteid}/{nombre_archivo}"
            urls.append(url)
        else:
            disponibles.append("NO")
            urls.append(None)

    df_cercanas['Disponible'] = disponibles
    df_cercanas['URL'] = urls
    return df_cercanas
