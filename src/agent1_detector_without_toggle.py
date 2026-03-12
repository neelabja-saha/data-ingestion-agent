import json
import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# ── Load environment variables ─────────────────────────────────────────────
load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR         = os.path.dirname(os.path.dirname(__file__))
LOGS_DIR         = os.path.join(BASE_DIR, "data", "logs")
ERROR_CODES_PATH = os.path.join(BASE_DIR, "data", "error_codes.json")

# ── Gemini client ──────────────────────────────────────────────────────────
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def load_error_codes():
    """Load error codes dictionary."""
    with open(ERROR_CODES_PATH, "r") as f:
        return json.load(f)


def load_all_logs():
    """Load all hourly log files from data/logs/."""
    all_jobs = []
    log_files = sorted([
        f for f in os.listdir(LOGS_DIR)
        if f.startswith("logs_hour_") and f.endswith(".json")
    ])

    print(f"\n  Loading {len(log_files)} log files...")
    for log_file in log_files:
        file_path = os.path.join(LOGS_DIR, log_file)
        with open(file_path, "r") as f:
            jobs = json.load(f)
            all_jobs.extend(jobs)
        print(f"  ✅ Loaded {log_file} — {len(jobs)} jobs")

    print(f"\n  Total jobs loaded: {len(all_jobs)}")
    return all_jobs


def detect_failures(all_jobs):
    """
    Scan all jobs and identify failed ones.
    Returns structured failure summary.
    """
    failed_jobs = [j for j in all_jobs if j["final_status"] == "FAILED"]
    completed_jobs = [j for j in all_jobs if j["final_status"] == "COMPLETED"]

    print(f"\n  Total jobs:     {len(all_jobs)}")
    print(f"  Completed:      {len(completed_jobs)}")
    print(f"  Failed:         {len(failed_jobs)}")
    print(f"  Failure rate:   {(len(failed_jobs)/len(all_jobs))*100:.1f}%")

    return failed_jobs, completed_jobs


def categorise_failures(failed_jobs, error_codes):
    """
    Categorise failed jobs by component, error code,
    failure stage and severity.
    """
    by_component  = {}
    by_error_code = {}
    by_stage      = {}
    by_severity   = {}

    for job in failed_jobs:
        error = job.get("error")
        if not error:
            continue

        component  = error.get("component", "Unknown")
        error_code = error.get("error_code", "Unknown")
        severity   = error.get("severity", "Unknown")

        # Get failure stage from status trail
        stage = "Unknown"
        trail = job.get("status_trail", [])
        for i, entry in enumerate(trail):
            if entry["status"] == "FAILED" and i > 0:
                stage = trail[i-1]["status"]
                break

        # Count by component
        by_component[component] = by_component.get(component, 0) + 1

        # Count by error code
        by_error_code[error_code] = by_error_code.get(error_code, 0) + 1

        # Count by stage
        by_stage[stage] = by_stage.get(stage, 0) + 1

        # Count by severity
        by_severity[severity] = by_severity.get(severity, 0) + 1

    return {
        "by_component":  by_component,
        "by_error_code": by_error_code,
        "by_stage":      by_stage,
        "by_severity":   by_severity
    }


def build_gemini_prompt(failed_jobs, categorisation, total_jobs):
    """
    Build a structured prompt for Gemini to analyse
    the failed jobs and identify key patterns.
    """
    # Send a sample of failed jobs to Gemini (max 50 to manage token usage)
    sample_size = min(50, len(failed_jobs))
    sample_jobs = failed_jobs[:sample_size]

    prompt = f"""
You are an expert Site Reliability Engineer (SRE) analysing data ingestion pipeline failures.

## Context
- Total jobs run: {total_jobs}
- Total failed jobs: {len(failed_jobs)}
- Overall failure rate: {(len(failed_jobs)/total_jobs)*100:.1f}%
- Sample size analysed: {sample_size} failed jobs

## Failure Distribution
By Component:
{json.dumps(categorisation['by_component'], indent=2)}

By Error Code:
{json.dumps(categorisation['by_error_code'], indent=2)}

By Failure Stage:
{json.dumps(categorisation['by_stage'], indent=2)}

By Severity:
{json.dumps(categorisation['by_severity'], indent=2)}

## Sample Failed Jobs (first {sample_size})
{json.dumps(sample_jobs, indent=2)}

## Your Task
Analyse the above failure data and provide:

1. PATTERN SUMMARY
   - What are the dominant failure patterns?
   - Are failures concentrated in specific components?
   - Is there a cascade effect (one failure causing others)?

2. TOP 3 ROOT CAUSES
   - Identify the top 3 most likely root causes
   - Explain the evidence supporting each root cause
   - Rate confidence level (High/Medium/Low)

3. INCIDENT ASSESSMENT
   - Is this a major incident or isolated failures?
   - What is the estimated business impact?
   - Which pipelines are most affected?

4. IMMEDIATE ACTIONS
   - List 3-5 immediate actions the SRE team should take
   - Prioritise by urgency (P1/P2/P3)

Be specific, technical, and actionable. Reference actual error codes and components from the data.
"""
    return prompt


def run_detector():
    """Main detector function — scans logs and identifies failures."""

    print("\n" + "="*55)
    print("  AGENT 1 — FAILURE DETECTOR")
    print("="*55)

    # Step 1 — Load all logs
    all_jobs = load_all_logs()

    # Step 2 — Detect failures
    print("\n" + "-"*55)
    print("  FAILURE DETECTION")
    print("-"*55)
    failed_jobs, completed_jobs = detect_failures(all_jobs)

    if not failed_jobs:
        print("\n  ✅ No failures detected. All jobs completed successfully.")
        return None

    # Step 3 — Categorise failures
    print("\n" + "-"*55)
    print("  FAILURE CATEGORISATION")
    print("-"*55)
    error_codes   = load_error_codes()
    categorisation = categorise_failures(failed_jobs, error_codes)

    print("\n  By Component:")
    for component, count in sorted(categorisation["by_component"].items(),
                                    key=lambda x: x[1], reverse=True):
        print(f"    {component:20} {count:5d} failures")

    print("\n  By Failure Stage:")
    for stage, count in sorted(categorisation["by_stage"].items(),
                                key=lambda x: x[1], reverse=True):
        print(f"    {stage:20} {count:5d} failures")

    print("\n  By Severity:")
    for severity, count in sorted(categorisation["by_severity"].items(),
                                   key=lambda x: x[1], reverse=True):
        print(f"    {severity:20} {count:5d} failures")

    print("\n  Top 10 Error Codes:")
    top_errors = sorted(categorisation["by_error_code"].items(),
                        key=lambda x: x[1], reverse=True)[:10]
    for code, count in top_errors:
        print(f"    {code:20} {count:5d} occurrences")

    # Step 4 — Run Gemini analysis
    print("\n" + "-"*55)
    print("  GEMINI ANALYSIS — IDENTIFYING PATTERNS")
    print("-"*55)
    print("  Sending failure data to Gemini for pattern analysis...")

    prompt   = build_gemini_prompt(failed_jobs, categorisation, len(all_jobs))
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    gemini_analysis = response.text

    print("  ✅ Gemini analysis complete")

    # Step 5 — Build output for Agent 2
    detection_output = {
        "scan_timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_jobs":       len(all_jobs),
        "total_completed":  len(completed_jobs),
        "total_failed":     len(failed_jobs),
        "failure_rate_pct": round((len(failed_jobs)/len(all_jobs))*100, 1),
        "categorisation":   categorisation,
        "failed_jobs":      failed_jobs,
        "gemini_analysis":  gemini_analysis
    }

    print("\n" + "="*55)
    print("  AGENT 1 COMPLETE")
    print("="*55)
    print(f"  Failed jobs identified : {len(failed_jobs)}")
    print(f"  Passing to Agent 2 for RCA...")
    print("="*55 + "\n")

    return detection_output


if __name__ == "__main__":
    result = run_detector()
    if result:
        print("\n  GEMINI PATTERN ANALYSIS:")
        print("  " + "-"*51)
        print(result["gemini_analysis"])
