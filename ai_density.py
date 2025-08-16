from __future__ import annotations
import numpy as np
import pandas as pd

def haversine(lat1, lon1, lat2, lon2):
    """
    Vektörize Haversine (km).
    lat/lon çiftleri derece cinsinden.
    """
    R = 6371.0
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (np.sin(dlat/2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2) ** 2)
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def density_score_for_line(line_coords, quakes_df: pd.DataFrame, radius_km=100.0):
    """
    LineString’in örnek noktaları için 'radius_km' içinde kalan deprem sayılarının ortalaması.
    """
    if quakes_df is None or len(quakes_df) == 0:
        return 0.0
    if not line_coords:
        return 0.0

    qlats = quakes_df["lat"].to_numpy(dtype=float)
    qlons = quakes_df["lon"].to_numpy(dtype=float)

    counts = []
    for lat, lon in line_coords:
        dists = haversine(lat, lon, qlats, qlons)
        counts.append(np.count_nonzero(dists <= float(radius_km)))

    if not counts:
        return 0.0

    return float(np.mean(counts))
