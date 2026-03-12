import os
import textwrap
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Colour palette ─────────────────────────────────────────────────────────
NAVY        = colors.HexColor("#1B2A4A")
CHARCOAL    = colors.HexColor("#2C3E50")
ACCENT_BLUE = colors.HexColor("#2980B9")
LIGHT_BLUE  = colors.HexColor("#D6EAF8")
RED         = colors.HexColor("#C0392B")
ORANGE      = colors.HexColor("#E67E22")
GREEN       = colors.HexColor("#27AE60")
LIGHT_GREY  = colors.HexColor("#F2F3F4")
MID_GREY    = colors.HexColor("#BDC3C7")
WHITE       = colors.white
BLACK       = colors.black

PAGE_W, PAGE_H = A4
MARGIN         = 20 * mm
CONTENT_WIDTH  = PAGE_W - 2 * MARGIN


def get_styles():
    """Define all paragraph styles."""
    styles = {
        # ── Cover page ──────────────────────────────────────────
        "title": ParagraphStyle(
            "title", fontSize=24, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
            spaceAfter=8, leading=30
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=13, textColor=WHITE,       # FIX 1: white on navy
            fontName="Helvetica-Bold", alignment=TA_CENTER, # FIX 4: bold
            spaceAfter=6, leading=18
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontSize=10, textColor=WHITE,     # FIX 1: white on navy
            fontName="Helvetica-Bold", alignment=TA_CENTER, # FIX 4: bold labels
            spaceAfter=4, leading=16
        ),
        "cover_meta_value": ParagraphStyle(
            "cover_meta_value", fontSize=10, textColor=WHITE, # FIX 1: white on navy
            fontName="Helvetica", alignment=TA_CENTER,
            spaceAfter=4, leading=16
        ),

        # ── Section headers ─────────────────────────────────────
        "section_title": ParagraphStyle(
            "section_title", fontSize=13, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_LEFT,   # FIX 4: bold
            spaceAfter=10, spaceBefore=4,
            backColor=NAVY, borderPad=8, leading=18
        ),
        "sub_heading": ParagraphStyle(
            "sub_heading", fontSize=10, textColor=NAVY,
            fontName="Helvetica-Bold", alignment=TA_LEFT,   # FIX 4: bold
            spaceAfter=4, spaceBefore=8, leading=14
        ),
        "component_heading": ParagraphStyle(
            "component_heading", fontSize=10, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_LEFT,   # FIX 4: bold
            spaceAfter=0, spaceBefore=10,
            backColor=CHARCOAL, borderPad=6, leading=14
        ),

        # ── Body text ───────────────────────────────────────────
        "body": ParagraphStyle(
            "body", fontSize=8.5, textColor=CHARCOAL,
            fontName="Helvetica", spaceAfter=4,
            leading=13, alignment=TA_LEFT
        ),
        "body_bold": ParagraphStyle(
            "body_bold", fontSize=8.5, textColor=CHARCOAL,
            fontName="Helvetica-Bold", spaceAfter=4,        # FIX 4: bold variant
            leading=13, alignment=TA_LEFT
        ),
        "body_small": ParagraphStyle(
            "body_small", fontSize=7.5, textColor=CHARCOAL,
            fontName="Helvetica", spaceAfter=3,
            leading=12, alignment=TA_LEFT
        ),

        # ── KPI ─────────────────────────────────────────────────
        "kpi_number": ParagraphStyle(
            "kpi_number", fontSize=20, textColor=NAVY,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
            leading=24
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", fontSize=7.5, textColor=CHARCOAL,
            fontName="Helvetica-Bold", alignment=TA_CENTER, # FIX 4: bold
            leading=11
        ),

        # ── Badge ───────────────────────────────────────────────
        "badge_p1": ParagraphStyle(
            "badge_p1", fontSize=12, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
            backColor=RED, borderPad=6, leading=16
        ),

        # ── Tables ──────────────────────────────────────────────
        "table_header": ParagraphStyle(
            "table_header", fontSize=8, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_LEFT,   # FIX 4: bold
            leading=12
        ),
        "table_cell": ParagraphStyle(
            "table_cell", fontSize=8, textColor=CHARCOAL,
            fontName="Helvetica", alignment=TA_LEFT,
            leading=12, wordWrap="CJK"
        ),
        "table_cell_small": ParagraphStyle(
            "table_cell_small", fontSize=7.5, textColor=CHARCOAL,
            fontName="Helvetica", alignment=TA_LEFT,
            leading=11, wordWrap="CJK"
        ),

        # ── Action items priority header ─────────────────────────
        "priority_header": ParagraphStyle(
            "priority_header", fontSize=9, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_LEFT,   # FIX 5: matches table width
            leading=13
        ),
    }
    return styles


def safe(text):
    """Escape XML special characters for safe ReportLab rendering."""
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def section_heading(title, styles):
    """
    Return a full-width navy Table containing the section title.
    This ensures the navy bar always stretches edge-to-edge,
    matching the width of all tables and infographics below it.
    """
    inner = ParagraphStyle(
        "sh_inner", fontSize=13, textColor=WHITE,
        fontName="Helvetica-Bold", alignment=TA_LEFT,
        leading=18, leftIndent=0
    )
    t = Table(
        [[Paragraph(title, inner)]],
        colWidths=[CONTENT_WIDTH]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ]))
    return t


def render_gemini_text(text, styles, heading_style="sub_heading", body_style="body"):
    """Convert Gemini markdown into ReportLab flowables."""
    flowables = []
    if not text:
        return flowables

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            flowables.append(Spacer(1, 2*mm))
            continue

        if line.startswith("### ") or line.startswith("## ") or line.startswith("# "):
            line = line.lstrip("#").strip().replace("**", "")
            flowables.append(Paragraph(safe(line), styles[heading_style]))
        elif line.startswith("---"):
            flowables.append(HRFlowable(
                width="100%", thickness=0.5, color=MID_GREY,
                spaceAfter=2, spaceBefore=2
            ))
        else:
            line = line.replace("*   ", "• ").replace("-   ", "• ")
            line = line.replace("•   ", "• ").replace("**", "")
            flowables.append(Paragraph(safe(line), styles[body_style]))

    return flowables


def build_bar_chart(component_data, total_failed, width=None):
    """
    Build horizontal bar chart.
    FIX 2: Shows percentage inside the bar and count to the right.
    """
    if width is None:
        width = CONTENT_WIDTH

    items   = sorted(component_data.items(), key=lambda x: x[1], reverse=True)
    max_val = max(v for _, v in items) if items else 1
    bar_h   = 18
    gap     = 7
    label_w = 100
    count_w = 50
    avail_w = int(width - label_w - count_w - 10)
    chart_h = len(items) * (bar_h + gap) + 10

    d = Drawing(width, chart_h)

    for i, (name, count) in enumerate(items):
        y     = chart_h - (i + 1) * (bar_h + gap)
        bar_w = max(4, int((count / max_val) * avail_w))
        pct   = round((count / total_failed) * 100, 1) if total_failed else 0

        # Component label (left)
        d.add(String(
            0, y + 4, name,
            fontName="Helvetica-Bold", fontSize=8,          # FIX 4: bold labels
            fillColor=CHARCOAL
        ))

        # Background track
        d.add(Rect(
            label_w, y, avail_w, bar_h,
            fillColor=LIGHT_BLUE, strokeColor=None
        ))

        # Filled bar
        d.add(Rect(
            label_w, y, bar_w, bar_h,
            fillColor=NAVY, strokeColor=None
        ))

        # FIX 2: Percentage inside the bar (white text)
        pct_label = f"{pct}%"
        pct_x     = label_w + max(4, bar_w / 2 - 10)
        if bar_w > 35:
            d.add(String(
                pct_x, y + 4, pct_label,
                fontName="Helvetica-Bold", fontSize=7,
                fillColor=WHITE
            ))

        # Count to the right of bar
        d.add(String(
            label_w + bar_w + 6, y + 4, str(count),
            fontName="Helvetica-Bold", fontSize=8,
            fillColor=CHARCOAL
        ))

    return d


def add_header_footer(canvas, doc):
    """Add navy header and grey footer to every page except cover."""
    if doc.page == 1:
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.restoreState()
        return

    canvas.saveState()

    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 14*mm, PAGE_W, 14*mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(WHITE)
    canvas.drawString(MARGIN, PAGE_H - 8.5*mm,
                      "DATA INGESTION ANOMALY AGENT — RCA REPORT")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 8.5*mm, "CONFIDENTIAL")

    # Footer bar
    canvas.setFillColor(LIGHT_GREY)
    canvas.rect(0, 0, PAGE_W, 9*mm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CHARCOAL)
    canvas.drawString(
        MARGIN, 3*mm,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  "
        f"Data Ingestion Anomaly Agent v1.0"
    )
    canvas.drawRightString(PAGE_W - MARGIN, 3*mm, f"Page {doc.page}")

    canvas.restoreState()


# ── Page builders ──────────────────────────────────────────────────────────

def build_cover(story, report, styles):
    """Page 1 — Cover page. FIX 1: All text white on navy background."""
    story.append(Spacer(1, 55*mm))

    # Title block — navy background
    title_data = [[Paragraph("DATA INGESTION ANOMALY AGENT", styles["title"])]]
    title_table = Table(title_data, colWidths=[CONTENT_WIDTH])
    title_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("TOPPADDING",    (0,0), (-1,-1), 18),
        ("BOTTOMPADDING", (0,0), (-1,-1), 18),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 6*mm))

    # Subtitle — white bold text (FIX 1 + FIX 4)
    story.append(Paragraph(
        "Automated Root Cause Analysis Report",
        styles["subtitle"]
    ))
    story.append(Spacer(1, 8*mm))

    # P1 badge
    badge_data = [[Paragraph("P1 — CRITICAL INCIDENT", styles["badge_p1"])]]
    badge_table = Table(badge_data, colWidths=[80*mm])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), RED),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ]))
    outer = Table([[badge_table]], colWidths=[CONTENT_WIDTH])
    outer.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER")]))
    story.append(outer)
    story.append(Spacer(1, 10*mm))

    # Metadata — FIX 1: all white text on navy background
    meta = report["metadata"]
    for label, value in [
        ("Period",         f"{meta['period_start']}  to  {meta['period_end']}"),
        ("Generated At",   meta["generated_at"]),
        ("Analysis Mode",  meta["analysis_mode"]),
        ("Report Version", "v1.0"),
    ]:
        row_data = [[
            Paragraph(safe(label), styles["cover_meta"]),
            Paragraph(safe(value), styles["cover_meta_value"]),
        ]]
        row_table = Table(row_data, colWidths=[50*mm, 110*mm])
        row_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), NAVY),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("LINEBELOW",     (0,0), (-1,-1), 0.3,
             colors.HexColor("#2C4A7A")),
            ("ALIGN",         (0,0), (0,0), "RIGHT"),
            ("ALIGN",         (1,0), (1,0), "LEFT"),
        ]))
        outer_row = Table([[row_table]], colWidths=[CONTENT_WIDTH])
        outer_row.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), NAVY),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 0),
            ("BOTTOMPADDING",(0,0), (-1,-1), 0),
        ]))
        story.append(outer_row)

    story.append(PageBreak())


def build_executive_summary(story, report, styles):
    """Page 2 — Executive summary."""
    summary = report["executive_summary"]
    total_f = summary["total_failed"]

    story.append(section_heading("EXECUTIVE SUMMARY", styles))
    story.append(Spacer(1, 4*mm))

    # KPI boxes
    def kpi_cell(number, label, bg):
        return Table(
            [[Paragraph(str(number), styles["kpi_number"])],
             [Paragraph(label,       styles["kpi_label"])]],
            style=[
                ("BACKGROUND",    (0,0), (-1,-1), bg),
                ("TOPPADDING",    (0,0), (-1,-1), 8),
                ("BOTTOMPADDING", (0,0), (-1,-1), 8),
                ("LEFTPADDING",   (0,0), (-1,-1), 4),
                ("RIGHTPADDING",  (0,0), (-1,-1), 4),
                ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ]
        )

    kpi_row = [[
        kpi_cell(summary["total_jobs"],              "Total Jobs",
                 LIGHT_BLUE),
        kpi_cell(summary["total_completed"],         "Completed",
                 colors.HexColor("#D5F5E3")),
        kpi_cell(summary["total_failed"],            "Failed",
                 colors.HexColor("#FADBD8")),
        kpi_cell(f"{summary['failure_rate_pct']}%",  "Failure Rate",
                 colors.HexColor("#FDEBD0")),
    ]]
    kpi_table = Table(kpi_row, colWidths=[CONTENT_WIDTH/4]*4)
    kpi_table.setStyle(TableStyle([
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("INNERGRID",     (0,0), (-1,-1), 0.5, WHITE),
        ("BOX",           (0,0), (-1,-1), 0.5, MID_GREY),
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 6*mm))

    # Severity breakdown
    story.append(Paragraph("Failure Severity Breakdown", styles["sub_heading"]))
    risk_map = {
        "Critical": "Immediate action required",
        "High":     "Urgent — action within hours",
        "Medium":   "Monitor closely",
        "Low":      "Low priority"
    }
    sev_rows = [[
        Paragraph("Severity",      styles["table_header"]),
        Paragraph("Count",         styles["table_header"]),
        Paragraph("% of Failures", styles["table_header"]),
        Paragraph("Risk Level",    styles["table_header"]),
    ]]
    for sev, count in sorted(summary["severity_breakdown"].items(),
                              key=lambda x: x[1], reverse=True):
        pct  = round((count / total_f) * 100, 1)
        sev_rows.append([
            Paragraph(safe(sev),              styles["table_cell"]),
            Paragraph(str(count),             styles["table_cell"]),
            Paragraph(f"{pct}%",              styles["table_cell"]),
            Paragraph(safe(risk_map.get(sev, "")), styles["table_cell"]),
        ])
    sev_table = Table(sev_rows, colWidths=[35*mm, 25*mm, 35*mm, 75*mm])
    sev_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), NAVY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID",          (0,0), (-1,-1), 0.4, MID_GREY),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(sev_table)
    story.append(Spacer(1, 6*mm))

    # Top 10 error codes
    story.append(Paragraph("Top 10 Error Codes", styles["sub_heading"]))
    err_rows = [[
        Paragraph("Rank",          styles["table_header"]),
        Paragraph("Error Code",    styles["table_header"]),
        Paragraph("Occurrences",   styles["table_header"]),
        Paragraph("% of Failures", styles["table_header"]),
    ]]
    for i, (code, count) in enumerate(report["top_error_codes"], 1):
        pct = round((count / total_f) * 100, 1)
        err_rows.append([
            Paragraph(str(i),     styles["table_cell"]),
            Paragraph(safe(code), styles["table_cell"]),
            Paragraph(str(count), styles["table_cell"]),
            Paragraph(f"{pct}%",  styles["table_cell"]),
        ])
    err_table = Table(err_rows, colWidths=[15*mm, 45*mm, 35*mm, 40*mm])
    err_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), CHARCOAL),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID",          (0,0), (-1,-1), 0.4, MID_GREY),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(err_table)
    story.append(PageBreak())


def build_pattern_analysis(story, report, styles):
    """Page 3 — Pattern analysis. FIX 2: % in bar. FIX 3: renamed heading."""
    story.append(section_heading("PATTERN ANALYSIS", styles))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("Failures by Component", styles["sub_heading"]))
    chart = build_bar_chart(
        report["executive_summary"]["component_breakdown"],
        report["executive_summary"]["total_failed"]   # FIX 2: pass total for %
    )
    story.append(chart)
    story.append(Spacer(1, 6*mm))

    # FIX 3: renamed from "Gemini Pattern Analysis" to "LLM Pattern Analysis"
    story.append(Paragraph("LLM Pattern Analysis", styles["sub_heading"]))
    story.append(HRFlowable(
        width="100%", thickness=1, color=NAVY,
        spaceAfter=3, spaceBefore=0
    ))
    story.append(Spacer(1, 2*mm))

    flowables = render_gemini_text(
        report["pattern_analysis"], styles,
        heading_style="sub_heading", body_style="body"
    )
    story.extend(flowables)
    story.append(PageBreak())


def build_component_rca(story, report, styles):
    """Component RCA pages."""
    story.append(section_heading("COMPONENT ROOT CAUSE ANALYSIS", styles))
    story.append(Spacer(1, 3*mm))
    analysis_note = (
        f"Analysis Mode: {report['metadata']['analysis_mode']}  |  "
        f"Sample: {report['metadata']['sample_pct']}%  |  "
        f"Jobs Analysed: {report['executive_summary']['jobs_analysed']} "
        f"of {report['executive_summary']['total_failed']}"
    )
    story.append(Paragraph(safe(analysis_note), styles["body_small"]))
    story.append(Spacer(1, 4*mm))

    for component, data in report["component_rca"].items():
        header_text = (
            f"  {component.upper()}  —  "
            f"{data['failure_count']} failures  "
            f"({data['pct_of_failures']}% of total)"
        )
        story.append(Paragraph(safe(header_text), styles["component_heading"]))
        story.append(Spacer(1, 2*mm))

        if data.get("top_error_codes"):
            codes = "  |  ".join([
                f"{c}: {n}" for c, n in data["top_error_codes"]
            ])
            story.append(Paragraph(
                f"Top Error Codes: {safe(codes)}",
                styles["body_small"]
            ))
            story.append(Spacer(1, 2*mm))

        flowables = render_gemini_text(
            data.get("gemini_rca", "No RCA data available."),
            styles,
            heading_style="sub_heading",
            body_style="body_small"
        )
        story.extend(flowables)
        story.append(Spacer(1, 3*mm))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=MID_GREY,
            spaceAfter=2, spaceBefore=2
        ))

    story.append(PageBreak())


def build_pipeline_impact(story, report, styles):
    """Pipeline impact page."""
    story.append(section_heading("PIPELINE IMPACT ASSESSMENT", styles))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("Pipeline Failure Ranking", styles["sub_heading"]))

    total_analysed = report["executive_summary"]["jobs_analysed"]

    headers = [
        Paragraph("Rank",            styles["table_header"]),
        Paragraph("Pipeline",        styles["table_header"]),
        Paragraph("Failures",        styles["table_header"]),
        Paragraph("% Analysed",      styles["table_header"]),
        Paragraph("Components Affected", styles["table_header"]),
    ]
    rows = [headers]
    for i, p in enumerate(report["pipeline_impact"], 1):
        pct = round((p["failure_count"] / total_analysed) * 100, 1) \
              if total_analysed else 0
        pipeline_name = p["pipeline"].replace("_to_bigquery", "")
        components    = "\n".join([
            f"{k}: {v}" for k, v in
            sorted(p["components_affected"].items(),
                   key=lambda x: x[1], reverse=True)
        ])
        rows.append([
            Paragraph(str(i),                 styles["table_cell"]),
            Paragraph(safe(pipeline_name),    styles["table_cell"]),
            Paragraph(str(p["failure_count"]),styles["table_cell"]),
            Paragraph(f"{pct}%",              styles["table_cell"]),
            Paragraph(safe(components),       styles["table_cell_small"]),
        ])

    pipeline_table = Table(
        rows, colWidths=[12*mm, 48*mm, 20*mm, 25*mm, 65*mm]
    )
    pipeline_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), NAVY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID",          (0,0), (-1,-1), 0.4, MID_GREY),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(pipeline_table)
    story.append(PageBreak())


def build_action_items(story, report, styles):
    """
    Action items page.
    FIX 5: Priority header rendered as first row of the table
            so header and table are always visually aligned.
    """
    story.append(section_heading("ACTION ITEMS", styles))
    story.append(Spacer(1, 4*mm))

    priority_colors = {"P1": RED, "P2": ORANGE, "P3": ACCENT_BLUE}
    priority_labels = {
        "P1": "P1 — Critical",
        "P2": "P2 — Urgent",
        "P3": "P3 — Important"
    }
    action_items = report["action_items"]

    for priority in ["P1", "P2", "P3"]:
        items = [a for a in action_items if a.get("priority") == priority]
        if not items:
            continue

        pc      = priority_colors.get(priority, NAVY)
        p_label = priority_labels.get(priority, priority)

        # FIX 5: Priority label as the very first row of the table
        # with a spanning background — header and table are one unit
        p_label_style = ParagraphStyle(
            f"pl_{priority}",
            fontSize=9, textColor=WHITE,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT, leading=13
        )
        col_header_style = ParagraphStyle(
            f"ch_{priority}",
            fontSize=8, textColor=WHITE,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT, leading=12
        )

        # Build all rows: priority title row + column headers + data rows
        all_rows = []

        # Row 0: priority title spanning all 4 columns
        all_rows.append([
            Paragraph(f"  {safe(p_label)}", p_label_style),
            "", "", ""
        ])

        # Row 1: column headers
        all_rows.append([
            Paragraph("Action",      col_header_style),
            Paragraph("Description", col_header_style),
            Paragraph("Owner",       col_header_style),
            Paragraph("Est. Time",   col_header_style),
        ])

        # Data rows
        for item in items:
            all_rows.append([
                Paragraph(safe(item.get("action", "")),
                          styles["table_cell"]),
                Paragraph(safe(item.get("description", "")),
                          styles["table_cell_small"]),
                Paragraph(safe(item.get("owner", "")),
                          styles["table_cell_small"]),
                Paragraph(safe(item.get("estimated_time", "")),
                          styles["table_cell_small"]),
            ])

        col_widths = [45*mm, 75*mm, 30*mm, 20*mm]
        action_table = Table(all_rows, colWidths=col_widths)
        action_table.setStyle(TableStyle([
            # Priority title row — spans all columns, priority colour
            ("SPAN",          (0,0), (3,0)),
            ("BACKGROUND",    (0,0), (3,0), pc),
            ("TOPPADDING",    (0,0), (3,0), 7),
            ("BOTTOMPADDING", (0,0), (3,0), 7),
            ("LEFTPADDING",   (0,0), (3,0), 6),

            # Column header row — charcoal background
            ("BACKGROUND",    (0,1), (-1,1), CHARCOAL),
            ("TOPPADDING",    (0,1), (-1,1), 5),
            ("BOTTOMPADDING", (0,1), (-1,1), 5),
            ("LEFTPADDING",   (0,1), (-1,1), 5),

            # Data rows — alternating
            ("ROWBACKGROUNDS",(0,2), (-1,-1), [WHITE, LIGHT_GREY]),
            ("TOPPADDING",    (0,2), (-1,-1), 5),
            ("BOTTOMPADDING", (0,2), (-1,-1), 5),
            ("LEFTPADDING",   (0,2), (-1,-1), 5),

            # Grid for entire table
            ("GRID",          (0,0), (-1,-1), 0.4, MID_GREY),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ]))
        story.append(action_table)
        story.append(Spacer(1, 5*mm))


# ── Main entry point ───────────────────────────────────────────────────────

def generate_pdf(report, output_path):
    """Generate the complete PDF report."""
    print(f"\n  Building PDF report...")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=20*mm,
        bottomMargin=15*mm,
        title="Data Ingestion Anomaly Agent — RCA Report",
        author="Data Ingestion Anomaly Agent v1.0"
    )

    styles = get_styles()
    story  = []

    print("  Building cover page...")
    build_cover(story, report, styles)

    print("  Building executive summary...")
    build_executive_summary(story, report, styles)

    print("  Building pattern analysis...")
    build_pattern_analysis(story, report, styles)

    print("  Building component RCA...")
    build_component_rca(story, report, styles)

    print("  Building pipeline impact...")
    build_pipeline_impact(story, report, styles)

    print("  Building action items...")
    build_action_items(story, report, styles)

    doc.build(
        story,
        onFirstPage=add_header_footer,
        onLaterPages=add_header_footer
    )

    print(f"  ✅ PDF saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    print("\n  ⚠️  pdf_generator.py is designed to be called from main.py")
    print("  Run main.py to execute the full pipeline.\n")
