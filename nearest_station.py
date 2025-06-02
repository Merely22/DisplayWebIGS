import pandas as pd
from geopy.distance import geodesic

def find_nearest_station(ruta_csv, lat, lon, n=2):
    df = pd.read_csv(ruta_csv, sep=",", header=0)
    df.columns = df.columns.str.strip().str.lower()
    

    df['distancia'] = df.apply(lambda row: geodesic((lat, lon), (row['latitude'], row['longitude'])).km, axis=1)
    df = df.sort_values(by='distancia')
    return df.head(n)
