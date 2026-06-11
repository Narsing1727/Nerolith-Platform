# Output Directory

Each simulation run creates a folder: output/runs/<run_id>/

Structure per run:
  manifest.json          â€” run metadata (start time, region count, config)
  snapshots/             â€” per-timestep grid + agent report snapshots
  alerts/                â€” all alerts issued during the run
  graph/                 â€” terrain graph used in this run
  report/
    summary.json         â€” structured risk assessment
    report.md            â€” narrative report from ReportAgent
  logs/
    run.log              â€” full run log
