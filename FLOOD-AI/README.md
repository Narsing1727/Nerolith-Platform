# FLOOD-AI â€” Intelligent Agent Layer

The AI observer layer that sits on top of the FLOOD-ENGINE physics simulation.

## Architecture

`
FLOOD-ENGINE (C++ DLL)          <-- physics: DEM, SWE, rainfall
      |
  engine_bridge/                <-- Python bridge to read DLL outputs
      |
  core/                         <-- session, region registry, data loader
      |
  agents/                       <-- regional observer agents
  |-- region_agent.py           <-- monitors one geographic zone
  |-- coordinator_agent.py      <-- global decision maker
  |-- report_agent.py           <-- generates final risk report
      |
  graph/                        <-- spatial knowledge graph of the terrain
  services/                     <-- LLM calls, memory, alert routing
  api/                          <-- REST API (FastAPI) consumed by Qt frontend
`

## Quick Start

`ash
cd FLOOD-AI
cp .env.example .env
pip install -r requirements.txt
python main.py
`
"@

New-File "FLOOD-AI\requirements.txt" @"
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
pydantic>=2.0.0
openai>=1.0.0
httpx>=0.27.0
numpy>=1.26.0
pandas>=2.0.0
networkx>=3.0
shapely>=2.0.0
python-dotenv>=1.0.0
loguru>=0.7.0
pytest>=8.0.0
