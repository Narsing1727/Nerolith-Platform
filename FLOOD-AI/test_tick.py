import sys
import os
import numpy as np
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from core.data_loader import load
from core.session import session
from core.region_registry import registry
from core.run_manager import init_run, finalize_run
from agents.agent_runner import agent_runner
from agents.alert_agent import alert_agent
from agents.report_agent import report_agent
from services.snapshot_store import snapshot_store
from services.alert_router import setup_default_channels
from graph.terrain_graph_builder import build_graph
from graph.graph_query import graph_query
from engine_bridge.engine_schema import (
    EngineTickPayload,
    FloodGridSnapshot,
    FlowGridSnapshot,
    RainfallGridSnapshot
)


GRID_ROWS = 100
GRID_COLS = 100
TIMESTEPS = 10


def make_flood_grid(timestep: int, hotspot_row: int = 20, hotspot_col: int = 20) -> list:
    grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=np.float64)

    # Rising flood centered on hotspot, spreading each timestep
    radius = 8 + timestep * 3
    intensity = 0.05 * timestep

    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            dist = np.sqrt((i - hotspot_row)**2 + (j - hotspot_col)**2)
            if dist < radius:
                grid[i, j] = intensity * (1 - dist / radius)

    # Add a second smaller flood zone in bottom-right
    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            dist2 = np.sqrt((i - 75)**2 + (j - 75)**2)
            if dist2 < 6 + timestep:
                grid[i, j] = max(grid[i, j], 0.02 * timestep)

    return grid.tolist()


def make_flow_grid(timestep: int) -> list:
    grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=np.float64)
    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            grid[i, j] = 0.1 + (timestep * 0.05) * np.random.random()
    return grid.tolist()


def make_rainfall_grid(timestep: int) -> list:
    grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=np.float64)
    intensity = 5.0 + timestep * 2.0
    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            grid[i, j] = intensity * np.random.uniform(0.7, 1.3)
    return grid.tolist()


def build_payload(timestep: int) -> EngineTickPayload:
    flood_data = make_flood_grid(timestep)
    flow_data  = make_flow_grid(timestep)
    rain_data  = make_rainfall_grid(timestep)

    flood_grid = FloodGridSnapshot(
        timestep=timestep,
        rows=GRID_ROWS,
        cols=GRID_COLS,
        cell_size_m=30.0,
        data=flood_data,
        max_depth_m=float(np.max(flood_data)),
        flooded_cell_count=int(np.sum(np.array(flood_data) > 0))
    )
    flow_grid = FlowGridSnapshot(
        timestep=timestep,
        rows=GRID_ROWS,
        cols=GRID_COLS,
        cell_size_m=30.0,
        data=flow_data,
        max_velocity_ms=float(np.max(flow_data))
    )
    rain_grid = RainfallGridSnapshot(
        timestep=timestep,
        rows=GRID_ROWS,
        cols=GRID_COLS,
        cell_size_m=30.0,
        data=rain_data,
        total_rainfall_mm=float(np.sum(rain_data))
    )

    return EngineTickPayload(
        timestep=timestep,
        elapsed_seconds=float(timestep * 300),
        flood=flood_grid,
        flow=flow_grid,
        rainfall=rain_grid
    )


def print_separator(char="─", width=60):
    print(char * width)


def run():
    print("\n")
    print_separator("═")
    print("  FLOOD-AI  —  Manual Tick Simulation Test")
    print_separator("═")

    # Boot sequence
    print("\n[BOOT] Loading terrain data...")
    load()
    print(f"[BOOT] {registry.count()} regions loaded.")

    print("[BOOT] Building graph...")
    G = build_graph()
    graph_query.load(G)
    print(f"[BOOT] Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print("[BOOT] Starting session...")
    run = session.start()
    session.set_region_count(registry.count())
    snapshot_store.set_run(run.run_id)
    setup_default_channels(run.run_id)
    init_run(run.run_id, registry.count())
    agent_runner.build_agents()
    print(f"[BOOT] Run ID: {run.run_id}")
    print(f"[BOOT] Agents built: {agent_runner.agent_count()}")

    print_separator()
    print(f"  Simulating {TIMESTEPS} timesteps — flood rising from top-left")
    print_separator()

    for t in range(1, TIMESTEPS + 1):
        payload = build_payload(t)
        decision = agent_runner.run_cycle(payload)
        session.tick()

        # Print timestep summary
        print(f"\n[T{t:02d}] Global Risk: {decision.global_risk.upper()}")

        # Show regions with risk > none
        active_risks = {
            rid: risk for rid, risk in decision.region_risks.items()
            if risk != "none"
        }
        if active_risks:
            print(f"      Regions at risk: {len(active_risks)}")
            for rid, risk in sorted(active_risks.items(), key=lambda x: x[1], reverse=True)[:5]:
                region = registry.get(rid)
                name = region.name if region else rid[:8]
                print(f"        {name:<15} → {risk.upper()}")

        # Show alerts fired this tick
        if decision.alerts_issued:
            print(f"      Alerts fired: {len(decision.alerts_issued)}")
            for alert in decision.alerts_issued[:3]:
                region = registry.get(alert.region_id)
                name = region.name if region else alert.region_id[:8]
                print(f"        [{alert.severity.upper()}] {name}: {alert.message[:60]}")

        # Show propagation warnings
        if decision.propagation_warnings:
            print(f"      Propagation: {len(decision.propagation_warnings)} downstream warnings")

        time.sleep(0.1)

    # Final summary
    print("\n")
    print_separator("═")
    print("  SIMULATION COMPLETE")
    print_separator("═")

    all_alerts = alert_agent.history()
    active    = alert_agent.active_alerts()
    latest    = snapshot_store.latest()

    print(f"\n  Total timesteps    : {TIMESTEPS}")
    print(f"  Total alerts fired : {len(all_alerts)}")
    print(f"  Active alerts now  : {len(active)}")
    if latest:
        print(f"  Final global risk  : {latest['global_risk'].upper()}")
        critical = [rid for rid, r in latest['region_risks'].items() if r == 'critical']
        high     = [rid for rid, r in latest['region_risks'].items() if r == 'high']
        print(f"  Critical regions   : {len(critical)}")
        print(f"  High risk regions  : {len(high)}")

    # Show memory of most affected region
    print("\n  Most affected region memory:")
    print_separator()
    worst_id = None
    worst_depth = 0.0
    for snap in snapshot_store.all():
        for rr in snap.get("region_reports", []):
            if rr["flood_max_m"] > worst_depth:
                worst_depth = rr["flood_max_m"]
                worst_id = rr["region_id"]

    if worst_id:
        agent = agent_runner.get_agent(worst_id)
        region = registry.get(worst_id)
        if agent and region:
            print(f"  Region : {region.name}")
            print(f"  Peak risk  : {agent.memory.peak_risk().upper()}")
            print(f"  Trend      : {agent.memory.flood_trend()}")
            print(f"  Max depth  : {worst_depth:.3f}m")
            events = agent.memory.long_term_events()
            if events:
                print(f"  Long-term events recorded: {len(events)}")
                for e in events[-3:]:
                    print(f"    T{e['timestep']:02d} | {e['risk_level'].upper()} | depth={e['max_flood_depth']:.3f}m")

    # Finalize
    session.stop()
    finalize_run(run.run_id, TIMESTEPS)

    print("\n")
    print_separator("═")
    print(f"  Run saved to: output/runs/{run.run_id}/")
    print("  Now run: python main.py")
    print("  Then hit: http://localhost:8000/docs")
    print_separator("═")
    print()


if __name__ == "__main__":
    run()