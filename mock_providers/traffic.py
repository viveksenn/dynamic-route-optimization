from math import radians, sin, cos, asin, sqrt
import numpy as np

EARTH_R_KM = 6371.0

def haversine_km(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1; dlon = lon2 - lon1
    h = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2*EARTH_R_KM*asin(sqrt(h))

def time_multiplier(epoch: int) -> float:
    seconds = epoch % 86400
    hour = seconds // 3600
    if 8 <= hour < 10 or 18 <= hour < 20:
        return 1.6
    if 9 <= hour < 11 or 17 <= hour < 19:
        return 1.4
    if 12 <= hour < 14:
        return 1.2
    return 1.0

def build_time_matrix(coords, departure_epoch):
    n = len(coords)
    M = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            if i == j:
                M[i, j] = 0
            else:
                dist_km = haversine_km(coords[i], coords[j])
                base_speed = 28.0  # km/h
                t = (dist_km / base_speed) * 3600.0
                t *= time_multiplier(departure_epoch)
                M[i, j] = max(int(t), 60)
    return M.tolist()