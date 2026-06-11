# Nerolith Terrain API - Project Structure Generator

$base = "nerolith-terrain"

$folders = @(
    "$base",
    "$base/api",
    "$base/api/routes",
    "$base/api/middleware",
    "$base/api/models",
    "$base/workers",
    "$base/workers/tasks",
    "$base/pipeline",
    "$base/pipeline/stages",
    "$base/mcp",
    "$base/mcp/tools",
    "$base/storage",
    "$base/ml",
    "$base/db",
    "$base/db/migrations",
    "$base/monitoring",
    "$base/config",
    "$base/tests",
    "$base/tests/api",
    "$base/tests/pipeline",
    "$base/tests/mcp"
)

$files = @(
    "$base/.env.example",
    "$base/docker-compose.yml",
    "$base/Dockerfile",
    "$base/requirements.txt",
    "$base/README.md",

    "$base/config/__init__.py",
    "$base/config/settings.py",

    "$base/api/__init__.py",
    "$base/api/main.py",
    "$base/api/routes/__init__.py",
    "$base/api/routes/terrain.py",
    "$base/api/routes/jobs.py",
    "$base/api/routes/health.py",
    "$base/api/middleware/__init__.py",
    "$base/api/middleware/auth.py",
    "$base/api/middleware/ratelimit.py",
    "$base/api/models/__init__.py",
    "$base/api/models/request.py",
    "$base/api/models/response.py",
    "$base/api/models/enums.py",

    "$base/workers/__init__.py",
    "$base/workers/celery_app.py",
    "$base/workers/tasks/__init__.py",
    "$base/workers/tasks/terrain_job.py",
    "$base/workers/tasks/webhook.py",

    "$base/pipeline/__init__.py",
    "$base/pipeline/orchestrator.py",
    "$base/pipeline/stages/__init__.py",
    "$base/pipeline/stages/source_select.py",
    "$base/pipeline/stages/fetch.py",
    "$base/pipeline/stages/datum_norm.py",
    "$base/pipeline/stages/void_fill.py",
    "$base/pipeline/stages/wang_liu.py",
    "$base/pipeline/stages/flow.py",
    "$base/pipeline/stages/derivatives.py",
    "$base/pipeline/stages/streams.py",
    "$base/pipeline/stages/confidence.py",
    "$base/pipeline/stages/cog_package.py",

    "$base/mcp/__init__.py",
    "$base/mcp/server.py",
    "$base/mcp/auth.py",
    "$base/mcp/tools/__init__.py",
    "$base/mcp/tools/analyze.py",
    "$base/mcp/tools/watershed.py",
    "$base/mcp/tools/flow_path.py",
    "$base/mcp/tools/nl_query.py",
    "$base/mcp/tools/job_status.py",
    "$base/mcp/tools/compare.py",

    "$base/storage/__init__.py",
    "$base/storage/s3.py",
    "$base/storage/signed_urls.py",
    "$base/storage/cache.py",

    "$base/ml/__init__.py",
    "$base/ml/superresolution.py",
    "$base/ml/nl_parser.py",

    "$base/db/__init__.py",
    "$base/db/models.py",
    "$base/db/session.py",
    "$base/db/migrations/.gitkeep",

    "$base/monitoring/__init__.py",
    "$base/monitoring/metrics.py",
    "$base/monitoring/logging.py",

    "$base/tests/__init__.py",
    "$base/tests/api/__init__.py",
    "$base/tests/api/test_terrain.py",
    "$base/tests/api/test_jobs.py",
    "$base/tests/pipeline/__init__.py",
    "$base/tests/pipeline/test_stages.py",
    "$base/tests/mcp/__init__.py",
    "$base/tests/mcp/test_tools.py"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

Write-Host "Nerolith Terrain project structure created." -ForegroundColor Green
Write-Host "Total folders: $($folders.Count)" -ForegroundColor Cyan
Write-Host "Total files: $($files.Count)" -ForegroundColor Cyan