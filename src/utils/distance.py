import math


def hitung_jarak_haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    rl1, rlo1 = math.radians(lat1), math.radians(lon1)
    rl2, rlo2 = math.radians(lat2), math.radians(lon2)
    dlat, dlon = rl2 - rl1, rlo2 - rlo1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rl1) * math.cos(rl2) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
