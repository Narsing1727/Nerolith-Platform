from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime

W, H = A4

C_BG      = HexColor("#0D1117")
C_ACCENT  = HexColor("#58A6FF")
C_GREEN   = HexColor("#3FB950")
C_YELLOW  = HexColor("#D29922")
C_RED     = HexColor("#F85149")
C_PINK    = HexColor("#FF6EB4")
C_TEXT    = HexColor("#E6EDF3")
C_MUTED   = HexColor("#8B949E")
C_SURFACE = HexColor("#161B22")
C_DIM     = HexColor("#21262D")

SEV_COLORS = {
    "critical": C_RED,
    "high":     C_YELLOW,
    "medium":   C_ACCENT,
    "low":      C_GREEN,
}

NODE_ICONS = {
    "SlopeStability": "01",
    "RiverBlockage":  "02",
    "DamBreach":      "03",
    "FloodWave":      "04",
}

NODE_DESC = {
    "SlopeStability": "Soil saturation exceeded failure threshold causing debris mobilization",
    "RiverBlockage":  "Debris volume sufficient to block river channel forming upstream lake",
    "DamBreach":      "Debris dam structural failure releasing stored lake volume",
    "FloodWave":      "High-velocity flood wave propagating downstream to settlements",
}


def bg_canvas(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(C_SURFACE)
    canvas.rect(0, 0, 4, H, fill=1, stroke=0)
    canvas.setFillColor(C_DIM)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawRightString(W - 20*mm, 12*mm, f"Page {doc.page}")
    canvas.drawString(20*mm, 12*mm, "NEROLITH — Cascade Failure Analysis Report")
    canvas.restoreState()


def build_styles():
    s = {}
    s["cover_title"] = ParagraphStyle("ct", fontName="Helvetica-Bold",
        fontSize=28, textColor=C_TEXT, leading=34, alignment=TA_LEFT)
    s["cover_sub"] = ParagraphStyle("cs", fontName="Helvetica",
        fontSize=12, textColor=C_MUTED, leading=16, alignment=TA_LEFT)
    s["cover_tag"] = ParagraphStyle("ctag", fontName="Helvetica-Oblique",
        fontSize=10, textColor=C_ACCENT, leading=14)
    s["section_label"] = ParagraphStyle("sl", fontName="Helvetica-Bold",
        fontSize=8, textColor=C_ACCENT, leading=10, spaceBefore=24, spaceAfter=2)
    s["section_title"] = ParagraphStyle("st", fontName="Helvetica-Bold",
        fontSize=18, textColor=C_TEXT, leading=24, spaceBefore=2, spaceAfter=12)
    s["body"] = ParagraphStyle("b", fontName="Helvetica",
        fontSize=10, textColor=C_TEXT, leading=16, spaceAfter=6)
    s["body_muted"] = ParagraphStyle("bm", fontName="Helvetica",
        fontSize=9.5, textColor=C_MUTED, leading=14, spaceAfter=4)
    s["node_title"] = ParagraphStyle("nt", fontName="Helvetica-Bold",
        fontSize=12, textColor=C_TEXT, leading=16, spaceBefore=16, spaceAfter=4)
    s["node_msg"] = ParagraphStyle("nm", fontName="Helvetica-Oblique",
        fontSize=10, textColor=C_MUTED, leading=14, spaceAfter=6)
    s["mono"] = ParagraphStyle("mono", fontName="Courier",
        fontSize=9, textColor=C_GREEN, leading=13, leftIndent=16, spaceAfter=3)
    s["warn"] = ParagraphStyle("w", fontName="Helvetica-Bold",
        fontSize=10, textColor=C_YELLOW, leading=14, spaceAfter=4)
    s["critical"] = ParagraphStyle("cr", fontName="Helvetica-Bold",
        fontSize=10, textColor=C_RED, leading=14, spaceAfter=4)
    s["table_header"] = ParagraphStyle("th", fontName="Helvetica-Bold",
        fontSize=9, textColor=C_TEXT, leading=12)
    s["table_cell"] = ParagraphStyle("tc", fontName="Helvetica",
        fontSize=9, textColor=C_TEXT, leading=12)
    s["arrival_title"] = ParagraphStyle("at", fontName="Helvetica-Bold",
        fontSize=11, textColor=C_PINK, leading=14, spaceBefore=12, spaceAfter=4)
    return s


def hr(color=C_SURFACE, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness,
                      color=color, spaceAfter=8, spaceBefore=4)


def sev_label(severity: str) -> str:
    return severity.upper()


def build_story(data: dict, S: dict) -> list:
    story = []
    events = data.get("events", [])
    sim    = data.get("simulation_params", {})
    region = data.get("region_id", "Unknown Region")
    ts     = data.get("timestep", 0)
    fired  = data.get("nodes_fired", len(events))
    ts_str = data.get("generated_at", datetime.utcnow().isoformat())[:19].replace("T", " ")

    # ── COVER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 50*mm))
    story.append(Paragraph("CASCADE FAILURE", S["cover_title"]))
    story.append(Paragraph("Analysis Report", S["cover_title"]))
    story.append(Spacer(1, 4*mm))
    story.append(hr(C_ACCENT, 1))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"Region: {region}  |  Timestep: {ts}  |  Generated: {ts_str}",
        S["cover_sub"]
    ))
    story.append(Spacer(1, 4*mm))

    overall_sev = "none"
    if events:
        sev_order = ["low", "medium", "high", "critical"]
        overall_sev = max(
            (e.get("severity", "low") for e in events),
            key=lambda x: sev_order.index(x) if x in sev_order else 0
        )

    sev_color = SEV_COLORS.get(overall_sev, C_MUTED)
    story.append(Paragraph(
        f"Overall Severity: {overall_sev.upper()}  |  Cascade Nodes Fired: {fired} / 4",
        S["cover_tag"]
    ))

    # ── EXECUTIVE SUMMARY ────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("EXECUTIVE SUMMARY", S["section_label"]))
    story.append(hr(C_DIM))

    if not events:
        story.append(Paragraph(
            "No cascade events triggered under current simulation conditions. "
            "Terrain and hydrological parameters do not meet failure thresholds.",
            S["body"]
        ))
    else:
        node_names = " → ".join(e.get("node", "") for e in events)
        story.append(Paragraph(
            f"A {overall_sev.upper()} severity cascade failure sequence was detected "
            f"in region {region} at simulation timestep {ts}. "
            f"The cascade propagated through {fired} node(s): {node_names}.",
            S["body"]
        ))
        if any(e.get("node") == "FloodWave" for e in events):
            wave = next(e for e in events if e.get("node") == "FloodWave")
            arrivals = wave.get("data", {}).get("arrival_times_min", {})
            if arrivals:
                earliest = min(arrivals.values())
                nearest  = min(arrivals, key=arrivals.get)
                story.append(Paragraph(
                    f"Flood wave will reach {nearest} in approximately {earliest:.1f} minutes. "
                    "Immediate evacuation of downstream settlements is recommended.",
                    S["critical"]
                ))

    # ── SIMULATION PARAMETERS ────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("SIMULATION PARAMETERS", S["section_label"]))
    story.append(hr(C_DIM))

    param_rows = [
        [Paragraph("Parameter", S["table_header"]),
         Paragraph("Value", S["table_header"]),
         Paragraph("Unit", S["table_header"])],
    ]
    param_data = [
        ("Soil Saturation",        f"{sim.get('soil_saturation', 0)*100:.1f}", "%"),
        ("Slope Angle",            f"{sim.get('slope_angle_deg', 0):.1f}", "degrees"),
        ("Slope Area",             f"{sim.get('slope_area_m2', 0):,.0f}", "m2"),
        ("Rainfall",               f"{sim.get('rainfall_mm', 0):.1f}", "mm"),
        ("Channel Width",          f"{sim.get('channel_width_m', 0):.1f}", "m"),
        ("Channel Depth",          f"{sim.get('channel_depth_m', 0):.1f}", "m"),
        ("Upstream Flow",          f"{sim.get('upstream_flow_m3s', 0):.1f}", "m3/s"),
        ("Lake Rise Rate",         f"{sim.get('lake_rise_rate_m_per_hr', 0):.2f}", "m/hr"),
        ("Manning's n",            f"{sim.get('manning_n', 0.035):.4f}", "-"),
        ("Channel Slope",          f"{sim.get('channel_slope', 0.002):.4f}", "m/m"),
    ]
    for name, val, unit in param_data:
        param_rows.append([
            Paragraph(name, S["table_cell"]),
            Paragraph(val,  S["table_cell"]),
            Paragraph(unit, S["table_cell"]),
        ])

    t = Table(param_rows, colWidths=[90*mm, 50*mm, 35*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  C_SURFACE),
        ("BACKGROUND",  (0, 1), (-1, -1), C_BG),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_BG, C_DIM]),
        ("TEXTCOLOR",   (0, 0), (-1, -1), C_TEXT),
        ("GRID",        (0, 0), (-1, -1), 0.3, C_DIM),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0,0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)

    if not events:
        return story

    # ── CASCADE CHAIN ────────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("CASCADE CHAIN", S["section_label"]))
    story.append(hr(C_DIM))
    story.append(Paragraph(
        "The following nodes fired in sequence. Each node's output becomes "
        "input to the next node in the chain.",
        S["body_muted"]
    ))

    all_nodes = ["SlopeStability", "RiverBlockage", "DamBreach", "FloodWave"]
    fired_names = {e.get("node") for e in events}

    for node_name in all_nodes:
        idx     = all_nodes.index(node_name)
        is_fired = node_name in fired_names
        icon    = NODE_ICONS.get(node_name, "?")
        event   = next((e for e in events if e.get("node") == node_name), None)

        status_char = "FIRED" if is_fired else "NOT TRIGGERED"
        status_col  = SEV_COLORS.get(event.get("severity", "low"), C_MUTED) if is_fired else C_MUTED

        story.append(Paragraph(
            f"Node {icon}  {node_name}  —  {status_char}",
            S["node_title"] if is_fired else S["body_muted"]
        ))

        story.append(Paragraph(NODE_DESC.get(node_name, ""), S["body_muted"]))

        if event:
            story.append(Paragraph(f"Message: {event.get('message', '')}", S["node_msg"]))
            story.append(Paragraph(
                f"Severity: {event.get('severity','').upper()}  |  "
                f"Probability: {event.get('probability', 0)*100:.1f}%",
                S["warn"] if event.get("severity") in ("high", "critical") else S["body"]
            ))

            d = event.get("data", {})
            for key, val in d.items():
                if key == "arrival_times_min":
                    continue
                label = key.replace("_", " ").title()
                if isinstance(val, float):
                    story.append(Paragraph(f"{label}: {val:.3f}", S["mono"]))
                else:
                    story.append(Paragraph(f"{label}: {val}", S["mono"]))

        if idx < len(all_nodes) - 1:
            story.append(Paragraph("↓", S["body_muted"]))

    # ── FLOOD WAVE ARRIVALS ──────────────────────────────────────────────────
    wave_event = next((e for e in events if e.get("node") == "FloodWave"), None)
    if wave_event:
        arrivals = wave_event.get("data", {}).get("arrival_times_min", {})
        if arrivals:
            story.append(Spacer(1, 4*mm))
            story.append(Paragraph("DOWNSTREAM ARRIVAL TIMES", S["section_label"]))
            story.append(hr(C_DIM))

            arr_rows = [
                [Paragraph("Settlement / Region", S["table_header"]),
                 Paragraph("Arrival Time (min)", S["table_header"]),
                 Paragraph("Urgency", S["table_header"])],
            ]
            for name, minutes in sorted(arrivals.items(), key=lambda x: x[1]):
                urgency = "IMMEDIATE" if minutes < 10 else "URGENT" if minutes < 30 else "MONITOR"
                arr_rows.append([
                    Paragraph(str(name), S["table_cell"]),
                    Paragraph(f"{minutes:.1f}", S["table_cell"]),
                    Paragraph(urgency, S["table_cell"]),
                ])

            at = Table(arr_rows, colWidths=[80*mm, 55*mm, 40*mm])
            at.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, 0),  C_SURFACE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_BG, C_DIM]),
                ("GRID",        (0, 0), (-1, -1), 0.3, C_DIM),
                ("TOPPADDING",  (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING",(0,0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(at)

    # ── RECOMMENDED ACTIONS ──────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("RECOMMENDED ACTIONS", S["section_label"]))
    story.append(hr(C_DIM))

    actions = []
    if "SlopeStability" in fired_names:
        actions.append("Deploy slope monitoring sensors on identified failure zones.")
        actions.append("Restrict access to hillside roads and settlements.")
    if "RiverBlockage" in fired_names:
        actions.append("Station rapid response teams at channel blockage point.")
        actions.append("Monitor lake water level continuously — install early warning gauge.")
    if "DamBreach" in fired_names:
        actions.append("Issue immediate downstream evacuation order.")
        actions.append("Notify emergency services — peak discharge exceeds safe channel capacity.")
    if "FloodWave" in fired_names:
        actions.append("Activate flood wave sirens in downstream settlements.")
        actions.append("Open emergency shelters on high ground above estimated wave depth.")

    for i, action in enumerate(actions, 1):
        story.append(Paragraph(f"{i}.  {action}", S["body"]))

    # ── FOOTER NOTE ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(hr(C_ACCENT, 0.8))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "This report was generated by the Nerolith FLOOD-AI Cascade Analysis Engine. "
        "Results are based on physics simulation outputs and should be validated "
        "against real-time field observations before operational decisions are made.",
        S["body_muted"]
    ))

    return story


def generate_cascade_pdf(data: dict, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm,  bottomMargin=18*mm,
        title="Nerolith Cascade Failure Analysis",
        author="FLOOD-AI"
    )
    S     = build_styles()
    story = build_story(data, S)
    doc.build(story, onFirstPage=bg_canvas, onLaterPages=bg_canvas)


# ── TEST ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        import json
        with open(sys.argv[1]) as f:
            data = json.load(f)
        generate_cascade_pdf(data, sys.argv[2])
        print(f"PDF saved: {sys.argv[2]}")
    else:
        
        generate_cascade_pdf(test_data, "cascade_report_test.pdf")
    test_data = {
        "region_id":    "roorkee_upper_ganga",
        "timestep":     14,
        "generated_at": datetime.utcnow().isoformat(),
        "nodes_fired":  4,
        "simulation_params": {
            "soil_saturation":        0.92,
            "slope_angle_deg":        38.0,
            "slope_area_m2":          20000.0,
            "rainfall_mm":            250.0,
            "channel_width_m":        20.0,
            "channel_depth_m":        4.0,
            "upstream_flow_m3s":      150.0,
            "lake_rise_rate_m_per_hr":1.2,
            "manning_n":              0.035,
            "channel_slope":          0.003,
        },
        "events": [
            {
                "node":        "SlopeStability",
                "severity":    "critical",
                "probability": 0.771,
                "message":     "Slope failure - saturation 92.0%, slope 38.0 deg. Debris 20160 m3 moving downhill.",
                "data": {
                    "soil_saturation":  0.92,
                    "slope_angle_deg":  38.0,
                    "debris_volume_m3": 20160.0,
                    "failure_depth_m":  3.36,
                    "rainfall_mm":      250.0,
                }
            },
            {
                "node":        "RiverBlockage",
                "severity":    "critical",
                "probability": 1.0,
                "message":     "River channel 100% blocked. Lake forming upstream - breach risk in 0.0h.",
                "data": {
                    "blockage_ratio":       1.0,
                    "debris_volume_m3":     20160.0,
                    "channel_width_m":      20.0,
                    "lake_formation_hours": 0.0,
                    "upstream_flow_m3s":    150.0,
                }
            },
            {
                "node":        "DamBreach",
                "severity":    "critical",
                "probability": 0.6,
                "message":     "Debris dam breaching - lake rising 1.20 m/hr. Peak 1657 m3/s in ~42 min.",
                "data": {
                    "lake_rise_rate_m_per_hr": 1.2,
                    "peak_discharge_m3s":      1657.0,
                    "breach_width_m":          33.6,
                    "time_to_peak_min":        42.0,
                    "lake_volume_m3":          80000.0,
                    "dam_height_m":            12.0,
                }
            },
            {
                "node":        "FloodWave",
                "severity":    "critical",
                "probability": 1.0,
                "message":     "Flood wave downstream - peak 1657 m3/s, speed 34.5 m/s, depth ~10.82 m.",
                "data": {
                    "peak_discharge_m3s": 1657.0,
                    "wave_celerity_ms":   34.5,
                    "max_depth_m":        10.82,
                    "arrival_times_min":  {
                        "village_A": 2.4,
                        "town_B":    7.2,
                        "city_C":    18.5,
                    },
                    "channel_width_m": 20.0,
                }
            },
        ]
    }

    out = "cascade_report_test.pdf"
    generate_cascade_pdf(test_data, out)
    print(f"PDF generated: {out}")