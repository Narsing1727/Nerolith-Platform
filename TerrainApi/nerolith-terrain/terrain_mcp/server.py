from mcp.server.fastmcp import FastMCP
from config.settings import settings
from terrain_mcp.tools.analyze import register_analyze_tool
from terrain_mcp.tools.job_status import register_job_status_tool
from terrain_mcp.tools.watershed import register_watershed_tool
from terrain_mcp.tools.flow_path import register_flow_path_tool

mcp = FastMCP(
    name="nerolith-terrain",
    instructions="""
    Nerolith Terrain MCP Server provides terrain intelligence tools for hydrology engineers and AI agents.
    Use analyze_terrain to process any area of interest and get hydrologically conditioned DEM data.
    Use get_job_status to poll the progress of a terrain analysis job.
    Use delineate_watershed to get watershed boundaries for any pour point.
    Use trace_flow_path to trace water flow from any coordinate downstream.
    """
)

register_analyze_tool(mcp)
register_job_status_tool(mcp)
register_watershed_tool(mcp)
register_flow_path_tool(mcp)