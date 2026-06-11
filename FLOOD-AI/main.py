
import os
import sys

from loguru import logger
import uvicorn

from config import settings
from core import data_loader
from core.session import session
from graph.terrain_graph_builder import build_graph, graph_to_schema
from graph.graph_storage import save_graph, load_graph
from graph.graph_query import graph_query
from agents.alert_agent import alert_agent
from services.alert_router import setup_default_channels, route
from api.router import create_app





def setup_logging():
    os.makedirs(settings.log_dir, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")
    logger.add(
        os.path.join(settings.log_dir, "flood_ai.log"),
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )


def setup_graph():
    cached = load_graph()
    if cached:
        logger.info("Loaded terrain graph from cache.")
        graph_query.load(cached)
        return

    logger.info("Building terrain graph from registry.")
    G = build_graph()
    graph_query.load(G)
    save_graph(G)
    logger.info(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")


def setup_alert_routing():
    run = session.get_run()
    run_id = run.run_id if run else "default"
    setup_default_channels(run_id)
    alert_agent.register_channel(route)


def main():
    setup_logging()
    logger.info("FLOOD-AI starting up.")

    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)

    data_loader.load()

    if session.get_run() is None:
        pass

    setup_graph()
    setup_alert_routing()

    app = create_app()

    logger.info(f"API server starting on {settings.agent_api_host}:{settings.agent_api_port}")

    uvicorn.run(
        app,
        host=settings.agent_api_host,
        port=settings.agent_api_port,
        log_level="warning"
    )


if __name__ == "__main__":
    main()