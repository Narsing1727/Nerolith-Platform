from enum import Enum


class LayerEnum(str, Enum):
    filled_dem = "filled_dem"
    flow_direction = "flow_direction"
    flow_accumulation = "flow_accumulation"
    twi = "twi"
    watershed = "watershed"
    stream_network = "stream_network"
    slope = "slope"
    aspect = "aspect"
    confidence = "confidence"


class OutputFormat(str, Enum):
    COG = "COG"
    GeoTIFF = "GeoTIFF"
    GeoJSON = "GeoJSON"


class AOIType(str, Enum):
    bbox = "bbox"
    polygon = "polygon"
    text = "text"


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"