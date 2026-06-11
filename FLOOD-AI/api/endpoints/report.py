"""
Report endpoints.
GET  /report/summary   â€” get the current risk summary (JSON)
GET  /report/markdown  â€” get the narrative report (markdown text)
POST /report/query     â€” ask the ReportAgent a natural language question
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.report_agent import report_agent
from core.session import session

router = APIRouter(prefix="/report", tags=["report"])


class QueryRequest(BaseModel):
    question: str


@router.post("/generate")
def generate_report():
    run = session.get_run()
    if not run:
        raise HTTPException(status_code=400, detail="No simulation run available.")
    return report_agent.generate(run.run_id)


@router.get("/summary")
def get_summary():
    data = report_agent.get_json()
    if not data:
        raise HTTPException(status_code=404, detail="No report generated yet.")
    return data


@router.get("/markdown")
def get_markdown():
    md = report_agent.get_markdown()
    if not md:
        raise HTTPException(status_code=404, detail="No report generated yet.")
    return {"report": md}


@router.post("/query")
def query_report(body: QueryRequest):
    return {"answer": report_agent.query(body.question)}