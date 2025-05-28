import pandas as pd
from geopy.distance import geodesic

def find_nearest_station(ruta_csv, lat, lon, n=2):
    df = pd.read_csv(ruta_csv, sep=";")

    df['distancia'] = df.apply(lambda row: geodesic((lat, lon), (row['Latitude'], row['Longitude'])).km, axis=1)
    df = df.sort_values(by='distancia')
    return df.head(n)
