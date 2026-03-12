import os
import sys
from datetime import datetime

# ── Add src to path so imports work ───────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent1_detector_with_toggle import run_detector
from agent2_reporter import run_reporter
from pdf_generator import generate_pdf

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def print_banner():
    """Print the main application banner."""
    print("\n" + "="*55)
    print("  DATA INGESTION ANOMALY AGENT")
    print("  Automated Root Cause Analysis Pipeline")
    print("="*55)
    print("  Version  : 1.0")
    print("  Model    : Gemini 2.5 Flash")
    print("  Authors  : Neelabja Saha")
    print("="*55 + "\n")


def get_report_filename():
    """Generate a timestamped report filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"rca_report_{timestamp}.pdf"


def run_pipeline():
    """
    Main pipeline — orchestrates Agent 1, Agent 2, and PDF generation.
    """
    print_banner()

    # ── Step 1: Run Agent 1 — Failure Detector ────────────────────────────
    print("  STEP 1 OF 3 — RUNNING AGENT 1 (FAILURE DETECTOR)")
    print("  " + "-"*51)
    detection_output = run_detector()

    if detection_output is None:
        print("\n  ✅ No failures detected or scan was cancelled.")
        print("  Pipeline complete — no report generated.\n")
        return

    # ── Step 2: Run Agent 2 — RCA Reporter ───────────────────────────────
    print("\n  STEP 2 OF 3 — RUNNING AGENT 2 (RCA REPORTER)")
    print("  " + "-"*51)
    report = run_reporter(detection_output)

    if report is None:
        print("\n  ❌ Agent 2 failed to generate report.")
        return

    # ── Step 3: Generate PDF ──────────────────────────────────────────────
    print("\n  STEP 3 OF 3 — GENERATING PDF REPORT")
    print("  " + "-"*51)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_filename = get_report_filename()
    output_path     = os.path.join(REPORTS_DIR, report_filename)

    generate_pdf(report, output_path)

    # ── Pipeline Complete ─────────────────────────────────────────────────
    print("\n" + "="*55)
    print("  PIPELINE COMPLETE")
    print("="*55)
    print(f"  Total jobs scanned  : {detection_output['total_jobs']}")
    print(f"  Total failures found: {detection_output['total_failed']}")
    print(f"  Failure rate        : {detection_output['failure_rate_pct']}%")
    print(f"  Analysis mode       : {detection_output['analysis_mode'].upper()}")
    print(f"  Report saved to     : reports/{report_filename}")
    print("="*55 + "\n")


if __name__ == "__main__":
    run_pipeline()
