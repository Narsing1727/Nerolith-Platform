import httpx
from config.settings import settings


def register_flow_path_tool(mcp):
    @mcp.tool()
    async def trace_flow_path(
        lat: float,
        lon: float,
        buffer_degrees: float = 0.3
    ) -> dict:
        """
        Trace the flow path from any coordinate downstream to the basin outlet.
        """
        bbox = [
            lon - buffer_degrees,
            lat - buffer_degrees,
            lon + buffer_degrees,
            lat + buffer_degrees
        ]
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://api:8000/terrain/v1/analyze",
                json={
                    "aoi": {"type": "bbox", "coordinates": bbox},
                    "layers": ["flow_direction", "flow_accumulation", "stream_network"],
                    "output_format": "COG",
                    "output_crs": "EPSG:4326"
                },
                headers={"Authorization": f"Bearer {settings.api_secret_key}"},
                timeout=30.0
            )
            return response.json()