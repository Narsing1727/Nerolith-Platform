import spacy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import re


nlp = spacy.load("en_core_web_sm")
geocoder = Nominatim(user_agent="nerolith-terrain", timeout=10)

LAYER_KEYWORDS = {
    "watershed": ["watershed", "basin", "catchment", "drainage"],
    "stream_network": ["stream", "river", "channel", "network"],
    "twi": ["wetness", "twi", "flood prone", "moisture", "saturated"],
    "flow_direction": ["flow", "direction", "routing"],
    "flow_accumulation": ["accumulation", "upstream", "contributing"],
    "slope": ["slope", "gradient", "steepness"],
    "aspect": ["aspect", "facing", "orientation"],
    "filled_dem": ["elevation", "terrain", "dem", "height"],
    "confidence": ["confidence", "quality", "accuracy"]
}

STRIP_WORDS = [
    "delineate", "show", "find", "trace", "analyze", "analyse",
    "upstream", "downstream", "near", "around", "the", "of", "in",
    "watershed", "basin", "catchment", "flow", "path", "terrain"
]

DEFAULT_BUFFER = 0.5


def extract_layers(query: str) -> list[str]:
    query_lower = query.lower()
    matched = []
    for layer, keywords in LAYER_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            matched.append(layer)
    if not matched:
        matched = ["filled_dem", "twi", "watershed", "stream_network"]
    return matched


def try_geocode(location: str) -> tuple[float, float] | None:
    try:
        result = geocoder.geocode(location)
        if result:
            return result.latitude, result.longitude
    except GeocoderTimedOut:
        pass
    return None


def extract_location(query: str) -> tuple[float, float] | None:
    doc = nlp(query)
    locations = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC", "FAC")]

    for location in locations:
        coords = try_geocode(location)
        if coords:
            return coords

    words = query.lower().split()
    cleaned = [w for w in words if w not in STRIP_WORDS]
    fallback_query = " ".join(cleaned).strip()
    if fallback_query:
        coords = try_geocode(fallback_query)
        if coords:
            return coords

    return None


def parse_nl_query(query: str) -> dict:
    layers = extract_layers(query)
    location = extract_location(query)

    if location:
        lat, lon = location
        bbox = [
            lon - DEFAULT_BUFFER,
            lat - DEFAULT_BUFFER,
            lon + DEFAULT_BUFFER,
            lat + DEFAULT_BUFFER
        ]
        description = f"Terrain analysis for location ({lat:.4f}, {lon:.4f})"
    else:
        bbox = [73.68, 18.41, 74.12, 18.89]
        description = "Default AOI used — no location detected in query"

    return {
        "bbox": bbox,
        "layers": layers,
        "description": description
    }