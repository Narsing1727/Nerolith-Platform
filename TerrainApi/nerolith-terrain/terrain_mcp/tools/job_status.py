import httpx
from config.settings import settings


def register_job_status_tool(mcp):
    @mcp.tool()
    async def get_job_status(job_id: str) -> dict:
        """
        Get the status of a terrain analysis job.
        Returns status, current stage, percent complete, and output paths when done.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://api:8000/terrain/v1/jobs/{job_id}",
                headers={"Authorization": f"Bearer {settings.api_secret_key}"},
                timeout=10.0
            )
            return response.json()