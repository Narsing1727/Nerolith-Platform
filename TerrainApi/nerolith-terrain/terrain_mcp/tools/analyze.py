import httpx
from config.settings import settings


def register_analyze_tool(mcp):
    @mcp.tool()
    async def analyze_terrain(
        bbox: list[float],
        layers: list[str] = ["filled_dem", "flow_direction", "flow_accumulation", "twi", "watershed", "stream_network", "slope", "confidence"],
        output_format: str = "COG",
        output_crs: str = "EPSG:4326"
    ) -> dict:
        """
        Analyze terrain for any area of interest.
        Returns a job_id to poll for results.
        bbox: [min_lon, min_lat, max_lon, max_lat]
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://api:8000/terrain/v1/analyze",
                json={
                    "aoi": {"type": "bbox", "coordinates": bbox},
                    "layers": layers,
                    "output_format": output_format,
                    "output_crs": output_crs
                },
                headers={"Authorization": f"Bearer {settings.api_secret_key}"},
                timeout=30.0
            )
            return response.json()