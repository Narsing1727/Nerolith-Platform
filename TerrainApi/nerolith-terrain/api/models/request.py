from pydantic import BaseModel, validator
from typing import Optional
from api.models.enums import LayerEnum, OutputFormat, AOIType

MAX_BBOX_AREA = 25.0


class AOI(BaseModel):
    type: AOIType
    coordinates: Optional[list[float]] = None
    geojson: Optional[dict] = None
    query: Optional[str] = None

    @validator("coordinates")
    def validate_bbox(cls, v, values):
        if values.get("type") == AOIType.bbox:
            if v is None or len(v) != 4:
                raise ValueError("bbox requires exactly 4 coordinates")
            if v[0] >= v[2] or v[1] >= v[3]:
                raise ValueError("invalid bbox bounds")
            if v[0] < -180 or v[2] > 180:
                raise ValueError("longitude out of range")
            if v[1] < -90 or v[3] > 90:
                raise ValueError("latitude out of range")
            area = (v[2] - v[0]) * (v[3] - v[1])
            if area > MAX_BBOX_AREA:
                raise ValueError(f"AOI too large. Max area is {MAX_BBOX_AREA} square degrees")
        return v

    @validator("query")
    def sanitize_query(cls, v):
        if v and len(v) > 500:
            raise ValueError("Query too long. Max 500 characters")
        return v


class TerrainRequest(BaseModel):
    aoi: AOI
    layers: list[LayerEnum] = list(LayerEnum)
    output_crs: str = "EPSG:4326"
    output_format: OutputFormat = OutputFormat.COG
    resolution: int = 30
    webhook_url: Optional[str] = None