import sys
import json
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 HRFlowable, Table, TableStyle)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Group
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker

W, H = A4

C_BG      = HexColor("#0D1117")
C_ACCENT  = HexColor("#58A6FF")
C_GREEN   = HexColor("#3FB950")
C_YELLOW  = HexColor("#D29922")
C_RED     = HexColor("#F85149")
C_CYAN    = HexColor("#00E5FF")
C_PURPLE  = HexColor("#B84CFF")
C_ORANGE  = HexColor("#FF8C00")
C_TEXT    = HexColor("#E6EDF3")
C_MUTED   = HexColor("#8B949E")
C_SURFACE = HexColor("#161B22")
C_DIM     = HexColor("#21262D")


def bg_canvas(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(C_SURFACE)
    canvas.rect(0, 0, 4, H, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(W - 20*mm, 12*mm, f"Page {doc.page}")
    canvas.drawString(20*mm, 12*mm, "NEROLITH — NeroSurrogate Batch Analysis Report")
    canvas.restoreState()


def S():
    return {
        "cover_title": ParagraphStyle("ct", fontName="Helvetica-Bold",
            fontSize=26, textColor=C_TEXT, leading=32),
        "cover_sub": ParagraphStyle("cs", fontName="Helvetica",
            fontSize=11, textColor=C_MUTED, leading=16),
        "cover_tag": ParagraphStyle("ctag", fontName="Helvetica-Oblique",
            fontSize=10, textColor=C_CYAN, leading=14),
        "section_label": ParagraphStyle("sl", fontName="Helvetica-Bold",
            fontSize=8, textColor=C_ACCENT, leading=10, spaceBefore=20, spaceAfter=2),
        "body": ParagraphStyle("b", fontName="Helvetica",
            fontSize=10, textColor=C_TEXT, leading=16, spaceAfter=6),
        "body_muted": ParagraphStyle("bm", fontName="Helvetica",
            fontSize=9.5, textColor=C_MUTED, leading=14, spaceAfter=4),
        "mono": ParagraphStyle("mono", fontName="Courier",
            fontSize=9, textColor=C_GREEN, leading=13, leftIndent=16, spaceAfter=3),
        "big_number": ParagraphStyle("bn", fontName="Helvetica-Bold",
            fontSize=22, textColor=C_CYAN, leading=28, alignment=TA_CENTER),
        "big_label": ParagraphStyle("bl", fontName="Helvetica",
            fontSize=9, textColor=C_MUTED, leading=12, alignment=TA_CENTER),
        "highlight_red": ParagraphStyle("hr2", fontName="Helvetica-Bold",
            fontSize=11, textColor=C_RED, leading=16, spaceAfter=4),
        "highlight_green": ParagraphStyle("hg", fontName="Helvetica-Bold",
            fontSize=11, textColor=C_GREEN, leading=16, spaceAfter=4),
        "highlight_yellow": ParagraphStyle("hy", fontName="Helvetica-Bold",
            fontSize=11, textColor=C_YELLOW, leading=16, spaceAfter=4),
        "highlight_cyan": ParagraphStyle("hc", fontName="Helvetica-Bold",
            fontSize=11, textColor=C_CYAN, leading=16, spaceAfter=4),
        "table_header": ParagraphStyle("th", fontName="Helvetica-Bold",
            fontSize=8, textColor=C_TEXT, leading=11),
        "table_cell": ParagraphStyle("tc", fontName="Helvetica",
            fontSize=8, textColor=C_TEXT, leading=11),
        "table_cell_green": ParagraphStyle("tcg", fontName="Helvetica-Bold",
            fontSize=8, textColor=C_GREEN, leading=11),
        "table_cell_red": ParagraphStyle("tcr", fontName="Helvetica-Bold",
            fontSize=8, textColor=C_RED, leading=11),
        "table_cell_yellow": ParagraphStyle("tcy", fontName="Helvetica-Bold",
            fontSize=8, textColor=C_YELLOW, leading=11),
        "table_cell_orange": ParagraphStyle("tco", fontName="Helvetica-Bold",
            fontSize=8, textColor=C_ORANGE, leading=11),
        "table_cell_muted": ParagraphStyle("tcm", fontName="Helvetica",
            fontSize=8, textColor=C_MUTED, leading=11),
    }


def hr(color=C_DIM, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness,
                      color=color, spaceAfter=8, spaceBefore=4)


def make_table(rows, col_widths, row_colors=None):
    t = Table(rows, colWidths=col_widths)
    style = [
        ("BACKGROUND",     (0, 0), (-1, 0),  C_SURFACE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_BG, C_DIM]),
        ("GRID",           (0, 0), (-1, -1), 0.3, C_DIM),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
    ]
    if row_colors:
        for row_idx, color in row_colors:
            style.append(("BACKGROUND", (0, row_idx), (-1, row_idx), color))
    t.setStyle(TableStyle(style))
    return t


def build_risk_chart(scenarios: list, width_mm=170, height_mm=60) -> Drawing:
    w = width_mm * mm
    h = height_mm * mm
    d = Drawing(w, h)

    pad_l, pad_r, pad_b, pad_t = 45, 10, 25, 10
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_b - pad_t

    d.add(Rect(0, 0, w, h, fillColor=C_SURFACE, strokeColor=None))
    d.add(Rect(pad_l, pad_b, plot_w, plot_h,
               fillColor=C_BG, strokeColor=C_DIM, strokeWidth=0.5))

    rain_vals  = [s["rainfall_mm_hr"] for s in scenarios]
    depth_vals = [s["max_depth_m"]    for s in scenarios]

    rain_min, rain_max = min(rain_vals), max(rain_vals)
    depth_min          = 0.0
    depth_max          = max(max(depth_vals) * 1.15, 0.1)

    def to_x(r):
        return pad_l + (r - rain_min) / max(rain_max - rain_min, 1) * plot_w

    def to_y(d_val):
        return pad_b + (d_val - depth_min) / max(depth_max - depth_min, 0.001) * plot_h

    n_x_ticks = 6
    for i in range(n_x_ticks + 1):
        r   = rain_min + i * (rain_max - rain_min) / n_x_ticks
        x   = to_x(r)
        d.add(Line(x, pad_b, x, pad_b + plot_h,
                   strokeColor=C_DIM, strokeWidth=0.3))
        d.add(String(x, pad_b - 10, f"{r:.0f}",
                     fontName="Helvetica", fontSize=7,
                     fillColor=C_MUTED, textAnchor="middle"))

    n_y_ticks = 4
    for i in range(n_y_ticks + 1):
        val = depth_min + i * (depth_max - depth_min) / n_y_ticks
        y   = to_y(val)
        d.add(Line(pad_l, y, pad_l + plot_w, y,
                   strokeColor=C_DIM, strokeWidth=0.3))
        d.add(String(pad_l - 4, y - 3, f"{val:.2f}",
                     fontName="Helvetica", fontSize=7,
                     fillColor=C_MUTED, textAnchor="end"))

    risk_colors = {"LOW": C_GREEN, "MEDIUM": C_ACCENT,
                   "HIGH": C_YELLOW, "CRITICAL": C_RED}
    for i in range(len(scenarios) - 1):
        s1, s2 = scenarios[i], scenarios[i + 1]
        x1, y1 = to_x(s1["rainfall_mm_hr"]), to_y(s1["max_depth_m"])
        x2, y2 = to_x(s2["rainfall_mm_hr"]), to_y(s2["max_depth_m"])
        color   = risk_colors.get(s1["risk_level"], C_GREEN)
        d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.5))

    d.add(String(pad_l + plot_w / 2, 4,
                 "Rainfall (mm/hr)",
                 fontName="Helvetica", fontSize=7,
                 fillColor=C_MUTED, textAnchor="middle"))
    d.add(String(8, pad_b + plot_h / 2,
                 "Max Depth (m)",
                 fontName="Helvetica", fontSize=7,
                 fillColor=C_MUTED, textAnchor="middle"))

    legend_x = pad_l + plot_w - 95
    legend_y  = pad_b + plot_h - 8
    for label, color in [("LOW", C_GREEN), ("MEDIUM", C_ACCENT),
                          ("HIGH", C_YELLOW), ("CRITICAL", C_RED)]:
        d.add(Rect(legend_x, legend_y, 8, 5,
                   fillColor=color, strokeColor=None))
        d.add(String(legend_x + 11, legend_y,
                     label, fontName="Helvetica", fontSize=6,
                     fillColor=C_TEXT))
        legend_x += 38

    return d


def risk_style_key(risk: str, styles: dict) -> str:
    return {
        "CRITICAL": "table_cell_red",
        "HIGH":     "table_cell_yellow",
        "MEDIUM":   "table_cell_orange",
        "LOW":      "table_cell_green",
    }.get(risk, "table_cell")


def build_story(data: dict, styles: dict) -> list:
    story = []

    ts_str    = data.get("timestamp", datetime.utcnow().isoformat())[:19].replace("T", " ")
    lat       = data.get("region_lat", 0.0)
    lon       = data.get("region_lon", 0.0)
    n_sc      = data.get("n_scenarios", 0)
    total_ms  = data.get("total_ms", 0.0)
    avg_ms    = data.get("avg_ms_per_scenario", 0.0)
    phys_s    = data.get("physics_est_total_s", n_sc * 45.0)
    speedup   = data.get("speedup_x", 0.0)
    rain_min  = data.get("rain_min", 10.0)
    rain_max  = data.get("rain_max", 150.0)
    crit_thr  = data.get("critical_threshold_mm")
    high_thr  = data.get("high_threshold_mm")
    med_thr   = data.get("medium_threshold_mm")
    max_depth = data.get("max_depth_overall", 0.0)
    rainfall  = data.get("rainfall_mm", 0.0)
    scenarios = data.get("scenarios", [])

    # ── COVER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 40*mm))
    story.append(Paragraph("NEROSURROGATE", styles["cover_title"]))
    story.append(Paragraph("Batch Flood Scenario Analysis", styles["cover_title"]))
    story.append(Spacer(1, 4*mm))
    story.append(hr(C_ACCENT, 1))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"Region: {lat:.4f}°N  {lon:.4f}°E  |  Generated: {ts_str}",
        styles["cover_sub"]
    ))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"Physics Engine: FloodEngine C++ DLL  |  "
        f"Surrogate: NeroSurrogate U-Net ONNX  |  "
        f"Rainfall Range: {rain_min:.0f} – {rain_max:.0f} mm/hr",
        styles["cover_tag"]
    ))

    # ── BIG NUMBERS ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("PERFORMANCE SUMMARY", styles["section_label"]))
    story.append(hr(C_DIM))

    big_rows = [[
        Paragraph(f"{n_sc}", styles["big_number"]),
        Paragraph(f"{total_ms/1000:.1f}s", styles["big_number"]),
        Paragraph(f"{phys_s/3600:.1f}hrs" if phys_s > 3600 else f"{phys_s:.0f}s",
                  styles["big_number"]),
        Paragraph(f"{speedup:.0f}x", styles["big_number"]),
    ],[
        Paragraph("Scenarios Run", styles["big_label"]),
        Paragraph("Surrogate Time", styles["big_label"]),
        Paragraph("Physics Est. Time", styles["big_label"]),
        Paragraph("Speedup", styles["big_label"]),
    ]]

    bt = Table(big_rows, colWidths=[42*mm, 42*mm, 42*mm, 42*mm])
    bt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_SURFACE),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_DIM),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, C_DIM),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(bt)

    # ── EXECUTIVE SUMMARY ────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("EXECUTIVE SUMMARY", styles["section_label"]))
    story.append(hr(C_DIM))
    story.append(Paragraph(
        f"NeroSurrogate analyzed {n_sc} flood scenarios for this terrain, "
        f"sweeping rainfall from {rain_min:.0f} to {rain_max:.0f} mm/hr. "
        f"Total inference time: {total_ms/1000:.1f} seconds ({avg_ms:.1f} ms/scenario). "
        f"Equivalent physics simulation would take approximately "
        f"{'%.1f hours' % (phys_s/3600) if phys_s > 3600 else '%.0f seconds' % phys_s} — "
        f"a {speedup:.0f}x speedup.",
        styles["body"]
    ))

    if crit_thr:
        story.append(Paragraph(
            f"CRITICAL RISK threshold crossed at {crit_thr:.1f} mm/hr rainfall. "
            f"Maximum predicted flood depth: {max_depth:.3f} m.",
            styles["highlight_red"]
        ))
    elif high_thr:
        story.append(Paragraph(
            f"HIGH RISK threshold crossed at {high_thr:.1f} mm/hr rainfall. "
            f"Maximum predicted flood depth: {max_depth:.3f} m.",
            styles["highlight_yellow"]
        ))
    elif med_thr:
        story.append(Paragraph(
            f"MEDIUM RISK begins at {med_thr:.1f} mm/hr rainfall. "
            "Region shows moderate flood resilience.",
            styles["highlight_cyan"]
        ))
    else:
        story.append(Paragraph(
            f"Region remains LOW RISK across all {n_sc} scenarios. "
            "Excellent flood resilience for tested rainfall range.",
            styles["highlight_green"]
        ))

    # ── RISK THRESHOLDS ──────────────────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("RISK THRESHOLD ANALYSIS", styles["section_label"]))
    story.append(hr(C_DIM))

    thresh_rows = [
        [Paragraph("Risk Level", styles["table_header"]),
         Paragraph("Rainfall Threshold", styles["table_header"]),
         Paragraph("Status", styles["table_header"]),
         Paragraph("Recommendation", styles["table_header"])],
        [Paragraph("MEDIUM", styles["table_cell_orange"]),
         Paragraph(f"{med_thr:.1f} mm/hr" if med_thr else "Not reached",
                   styles["table_cell"]),
         Paragraph("REACHED" if med_thr else "SAFE", 
                   styles["table_cell_yellow"] if med_thr else styles["table_cell_green"]),
         Paragraph("Monitor drainage systems", styles["table_cell"])],
        [Paragraph("HIGH", styles["table_cell_yellow"]),
         Paragraph(f"{high_thr:.1f} mm/hr" if high_thr else "Not reached",
                   styles["table_cell"]),
         Paragraph("REACHED" if high_thr else "SAFE",
                   styles["table_cell_red"] if high_thr else styles["table_cell_green"]),
         Paragraph("Pre-position emergency teams", styles["table_cell"])],
        [Paragraph("CRITICAL", styles["table_cell_red"]),
         Paragraph(f"{crit_thr:.1f} mm/hr" if crit_thr else "Not reached",
                   styles["table_cell"]),
         Paragraph("REACHED" if crit_thr else "SAFE",
                   styles["table_cell_red"] if crit_thr else styles["table_cell_green"]),
         Paragraph("Issue evacuation order", styles["table_cell"])],
    ]
    story.append(make_table(thresh_rows, [35*mm, 45*mm, 30*mm, 65*mm]))

    # ── RISK CURVE CHART ─────────────────────────────────────────────────────
    if scenarios:
        story.append(Spacer(1, 6*mm))
        story.append(Paragraph("FLOOD DEPTH vs RAINFALL — RISK CURVE", styles["section_label"]))
        story.append(hr(C_DIM))
        story.append(Paragraph(
            "Each point represents one surrogate scenario. "
            "Color indicates risk level: GREEN=Low, BLUE=Medium, YELLOW=High, RED=Critical.",
            styles["body_muted"]
        ))
        story.append(Spacer(1, 2*mm))

        sc_dicts = [s if isinstance(s, dict) else s.dict() for s in scenarios]
        chart    = build_risk_chart(sc_dicts, width_mm=170, height_mm=65)
        story.append(chart)

    # ── SCENARIO SAMPLE TABLE ────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("SCENARIO RESULTS — SAMPLE (every 10th)", styles["section_label"]))
    story.append(hr(C_DIM))

    sample_rows = [
        [Paragraph("#",           styles["table_header"]),
         Paragraph("Rainfall",    styles["table_header"]),
         Paragraph("Max Depth",   styles["table_header"]),
         Paragraph("Flooded %",   styles["table_header"]),
         Paragraph("High Risk",   styles["table_header"]),
         Paragraph("Risk Level",  styles["table_header"])],
    ]

    step = max(1, len(scenarios) // 20)
    row_colors = []
    for i, s in enumerate(scenarios[::step]):
        s_dict   = s if isinstance(s, dict) else s.dict()
        risk     = s_dict["risk_level"]
        style_key = risk_style_key(risk, styles)
        row_colors.append((i + 1, {
            "CRITICAL": HexColor("#2D1517"),
            "HIGH":     HexColor("#2D2500"),
            "MEDIUM":   HexColor("#0D1A2D"),
            "LOW":      HexColor("#0D1117"),
        }.get(risk, C_BG)))
        sample_rows.append([
            Paragraph(str(s_dict["scenario_id"]),          styles["table_cell_muted"]),
            Paragraph(f"{s_dict['rainfall_mm_hr']:.1f} mm", styles["table_cell"]),
            Paragraph(f"{s_dict['max_depth_m']:.3f} m",    styles["table_cell"]),
            Paragraph(f"{s_dict['flooded_fraction']*100:.2f}%", styles["table_cell"]),
            Paragraph(str(s_dict["high_risk_cells"]),       styles["table_cell"]),
            Paragraph(risk, styles[style_key]),
        ])

    story.append(make_table(
        sample_rows,
        [12*mm, 30*mm, 30*mm, 28*mm, 28*mm, 30*mm],
        row_colors
    ))

    # ── SURROGATE vs PHYSICS ─────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("SURROGATE vs PHYSICS ENGINE", styles["section_label"]))
    story.append(hr(C_DIM))

    comp_rows = [
        [Paragraph("Method",     styles["table_header"]),
         Paragraph("N Scenarios", styles["table_header"]),
         Paragraph("Total Time", styles["table_header"]),
         Paragraph("Per Scenario", styles["table_header"]),
         Paragraph("Suitable For", styles["table_header"])],
        [Paragraph("FloodEngine DLL\n(C++ Physics)", styles["table_cell"]),
         Paragraph(str(n_sc), styles["table_cell"]),
         Paragraph(f"{'%.1f hrs' % (phys_s/3600) if phys_s > 3600 else '%.0f sec' % phys_s}",
                   styles["table_cell_red"]),
         Paragraph("~45 sec", styles["table_cell"]),
         Paragraph("Final validation, accurate results", styles["table_cell"])],
        [Paragraph("NeroSurrogate\n(U-Net ONNX)", styles["table_cell"]),
         Paragraph(str(n_sc), styles["table_cell"]),
         Paragraph(f"{total_ms/1000:.1f} sec", styles["table_cell_green"]),
         Paragraph(f"{avg_ms:.1f} ms", styles["table_cell_green"]),
         Paragraph("Real-time what-if, batch analysis", styles["table_cell"])],
    ]
    story.append(make_table(comp_rows, [40*mm, 25*mm, 30*mm, 30*mm, 50*mm]))

    # ── METHODOLOGY ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("METHODOLOGY", styles["section_label"]))
    story.append(hr(C_DIM))

    for item in [
        "DEM loaded from OpenTopography SRTM/COP30 via GDAL, scaled to training range",
        "6-channel input tensor: DEM elevation, terrain slope, D8 flow accumulation, rainfall, soil moisture, Manning's n",
        "U-Net: 4 encoder/decoder levels, skip connections, BatchNorm, ~7.7M parameters",
        "Training: 1,000 FloodEngine DLL scenarios, Latin Hypercube Sampling over 7 parameters",
        "Combined loss: MSE (weight=0.7) + IoU (weight=0.3) over 100 epochs",
        "ONNX export, CPU inference via onnxruntime, single-thread optimized",
        f"Validation IoU: 0.83 | Rainfall sweep: {rain_min:.0f}–{rain_max:.0f} mm/hr in {n_sc} steps",
    ]:
        story.append(Paragraph(f"• {item}", styles["body_muted"]))

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(hr(C_ACCENT, 0.8))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "Generated by Nerolith NeroSurrogate ML Engine. "
        "Surrogate predictions approximate physics simulation (~85-90% accuracy). "
        "Validate critical findings with full FloodEngine simulation.",
        styles["body_muted"]
    ))

    return story


def generate_surrogate_pdf(data: dict, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm,  bottomMargin=18*mm,
        title="Nerolith NeroSurrogate Batch Analysis",
        author="FLOOD-AI"
    )
    styles = S()
    story  = build_story(data, styles)
    doc.build(story, onFirstPage=bg_canvas, onLaterPages=bg_canvas)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        with open(sys.argv[1]) as f:
            data = json.load(f)
        generate_surrogate_pdf(data, sys.argv[2])
        print(f"PDF saved: {sys.argv[2]}")
    else:
        print("Usage: python surrogate_pdf.py input.json output.pdf")