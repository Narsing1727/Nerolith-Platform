"""
ReportAgent: generates the final risk report after simulation.
- Has access to full simulation history (all timestep snapshots)
- Uses LLM to write natural-language risk summaries per region
- Produces structured JSON report + human-readable markdown
- Can be queried interactively: 'Why is Zone 3 high risk?'
Inspired by MiroFish's ReportAgent with rich toolset pattern.
"""
from services.snapshot_store import snapshot_store
from services.llm_client import ask
from core.region_registry import registry
from core.schemas import RiskLevel
from config import settings
import json
import os
from typing import Optional
from loguru import logger


SYSTEM_PROMPT = """You are a senior flood risk analyst AI.
You analyze flood simulation data and write precise, technical risk reports.
Be factual. Reference specific regions, depths, and trends.
Never speculate beyond the data provided."""


class ReportAgent:
    def __init__(self):
        self._report_md: Optional[str] = None
        self._report_json: Optional[dict] = None

    def generate(self, run_id: str) -> dict:
        snapshots = snapshot_store.all()
        if not snapshots:
            return {"error": "no_snapshots_available"}

        summary = self._build_summary(snapshots)
        narrative = self._write_narrative(summary)

        self._report_json = summary
        self._report_md = narrative

        self._save(run_id, summary, narrative)

        return summary

    def query(self, question: str) -> str:
        if not self._report_json:
            return "No simulation report available yet. Run the simulation first."

        context = json.dumps(self._report_json, indent=2)
        prompt = f"""Simulation report context:
{context}

Question: {question}

Answer based strictly on the data above."""

        return ask(prompt, system=SYSTEM_PROMPT) or "Unable to answer at this time."

    def get_markdown(self) -> Optional[str]:
        return self._report_md

    def get_json(self) -> Optional[dict]:
        return self._report_json

    def _build_summary(self, snapshots: list) -> dict:
        region_peak: dict = {}
        region_max_depth: dict = {}
        total_alerts = 0

        for snap in snapshots:
            total_alerts += snap.get("alerts_count", 0)
            for rr in snap.get("region_reports", []):
                rid = rr["region_id"]
                risk = rr["risk_level"]
                depth = rr.get("flood_max_m", 0)

                order = [r.value for r in RiskLevel]
                if rid not in region_peak or order.index(risk) > order.index(region_peak[rid]):
                    region_peak[rid] = risk

                if rid not in region_max_depth or depth > region_max_depth[rid]:
                    region_max_depth[rid] = depth

        critical_regions = [rid for rid, r in region_peak.items() if r == RiskLevel.CRITICAL]
        high_regions = [rid for rid, r in region_peak.items() if r == RiskLevel.HIGH]

        overall = RiskLevel.NONE.value
        for rid, r in region_peak.items():
            order = [rv.value for rv in RiskLevel]
            if order.index(r) > order.index(overall):
                overall = r

        return {
            "run_summary": {
                "total_timesteps": len(snapshots),
                "total_alerts": total_alerts,
                "overall_risk": overall,
                "critical_regions": critical_regions,
                "high_risk_regions": high_regions
            },
            "region_peaks": region_peak,
            "region_max_depths_m": region_max_depth
        }

    def _write_narrative(self, summary: dict) -> str:
        prompt = f"""Write a professional flood risk assessment report based on this simulation summary:

{json.dumps(summary, indent=2)}

Structure:
1. Executive Summary (2-3 sentences)
2. Critical Findings (bullet points)
3. Region-by-Region Assessment
4. Recommended Actions

Be concise and technical."""

        result = ask(prompt, system=SYSTEM_PROMPT, max_tokens=2000)
        return result or "Report generation failed."

    def _save(self, run_id: str, summary: dict, narrative: str):
        path = os.path.join(settings.output_dir, "runs", run_id, "report")
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)
        with open(os.path.join(path, "report.md"), "w") as f:
            f.write(narrative)

    def reset(self):
        self._report_md = None
        self._report_json = None


report_agent = ReportAgent()