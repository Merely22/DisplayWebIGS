from geopy.distance import geodesic 
import pandas as pd

def find_nearest_station(lat, lon, stations_df):
    user_location = (lat, lon)

    # Calculate distance for each station
    stations_df["Distance_km"] = stations_df.apply(
        lambda row: geodesic(user_location, (row["Latitude"], row["Longitude"])).kilometers,
        axis=1
    )

    # Sort by distance and get 2 nearest
    nearest_two = stations_df.sort_values("Distance_km").head(2).copy()

    return nearest_two
