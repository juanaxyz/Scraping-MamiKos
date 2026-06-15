BASE_URL = "https://mamikos.com/cari/"

SESSION_FILE = "sessions/mamikos_session.json"
OUTPUT_FILE = "data/raw/mamikos_data_unud_sudirman.json"
FAILED_POI_FILE = "data/failed/failed_poi_unud_sudirman.json"

MAX_CARDS_TO_TEST = 3

REKTORAT_UNUD = [-8.798256245751867, 115.17249471428231]
UNUD_SUDIRMAN = [-8.673060417640015, 115.21901203994138]
BANDARA_IGUSTI_NGURAH_RAI = [-8.745770625116275, 115.16783601042454]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
OVERPASS_QUERY_TIMEOUT = 25
OVERPASS_HTTP_TIMEOUT = 30
OVERPASS_INTER_REQUEST_DELAY = 1.5
OVERPASS_MAX_RETRIES = 2

RETRY_OVERPASS_HTTP_TIMEOUT = 35
RETRY_OVERPASS_MAX_RETRIES = 3
RETRY_INTER_REQUEST_DELAY = 5.0
RETRY_INTER_KOS_DELAY = 10.0

ENABLE_POI_ENRICHMENT = True

_POI_FAILED = "__FAILED__"

POI_CATEGORIES = {
    "university": {"tags": [("amenity", "university")], "radius": 10000},
    "hospital": {"tags": [("amenity", "hospital")], "radius": 10000},
    "supermarket": {"tags": [("shop", "supermarket")], "radius": 10000},
    "terminal": {"tags": [("amenity", "bus_station")], "radius": 10000},
    "mall": {"tags": [("shop", "mall")], "radius": 10000},
    "clinic": {"tags": [("amenity", "clinic")], "radius": 10000},
}

POI_DISTANCE_CACHE: dict = {}
