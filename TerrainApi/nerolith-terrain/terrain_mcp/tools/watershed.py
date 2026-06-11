import httpx
from config.settings import settings


def register_watershed_tool(mcp):
    @mcp.tool()
    async def delineate_watershed(
        lat: float,
        lon: float,
        buffer_degrees: float = 0.5
    ) -> dict:
        """
        Delineate watershed boundary for any pour point.
        lat/lon: coordinates of the outlet point.
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
                    "layers": ["watershed", "stream_network", "flow_direction"],
                    "output_format": "COG",
                    "output_crs": "EPSG:4326"
                },
                headers={"Authorization": f"Bearer {settings.api_secret_key}"},
                timeout=30.0
            )
            return response.json()