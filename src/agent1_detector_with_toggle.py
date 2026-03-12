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

# ── Token & cost estimates ─────────────────────────────────────────────────
TOKENS_PER_JOB    = 550   # approximate tokens per failed job log
INPUT_COST_PER_1M = 0.10  # Gemini 2.5 Flash input cost per 1M tokens (USD)


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
    """Scan all jobs and identify failed ones."""
    failed_jobs    = [j for j in all_jobs if j["final_status"] == "FAILED"]
    completed_jobs = [j for j in all_jobs if j["final_status"] == "COMPLETED"]

    print(f"\n  Total jobs:     {len(all_jobs)}")
    print(f"  Completed:      {len(completed_jobs)}")
    print(f"  Failed:         {len(failed_jobs)}")
    print(f"  Failure rate:   {(len(failed_jobs)/len(all_jobs))*100:.1f}%")

    return failed_jobs, completed_jobs


def categorise_failures(failed_jobs):
    """
    Categorise ALL failed jobs by component, error code,
    failure stage and severity.
    Always runs on 100% of failures regardless of analysis mode.
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

        by_component[component]   = by_component.get(component, 0) + 1
        by_error_code[error_code] = by_error_code.get(error_code, 0) + 1
        by_stage[stage]           = by_stage.get(stage, 0) + 1
        by_severity[severity]     = by_severity.get(severity, 0) + 1

    return {
        "by_component":  by_component,
        "by_error_code": by_error_code,
        "by_stage":      by_stage,
        "by_severity":   by_severity
    }


def estimate_cost(num_jobs):
    """Estimate Gemini API cost for a given number of jobs."""
    estimated_tokens = num_jobs * TOKENS_PER_JOB
    estimated_cost   = (estimated_tokens / 1_000_000) * INPUT_COST_PER_1M
    return estimated_tokens, estimated_cost


def show_analysis_menu(total_failed):
    """
    Show analysis mode selection menu.
    Returns mode and sample_pct chosen by user.
    """
    print("\n" + "="*55)
    print("  SELECT ANALYSIS MODE")
    print("="*55)
    print(f"  Total failed jobs available: {total_failed}")
    print()
    print("  [1] SAMPLE MODE")
    print("      Analyse a % of failed jobs")
    print("      Faster · Lower cost")
    print("      Good for quick health checks")
    print()
    print("  [2] FULL SCAN MODE")
    print("      Analyse all failed jobs")
    print("      Complete coverage · Higher accuracy")
    print("      Recommended for incident RCA")
    print("="*55)

    while True:
        choice = input("\n  Enter choice (1 or 2): ").strip()
        if choice in ["1", "2"]:
            break
        print("  ❌ Invalid choice. Please enter 1 or 2.")

    if choice == "1":
        # ── Sample Mode ────────────────────────────────────────
        print("\n" + "-"*55)
        pct = None  # initialise before while loop to fix scoping
        while True:
            try:
                pct = int(input("  Enter sample percentage (1-100): ").strip())
                if 1 <= pct <= 100:
                    break
                print("  ❌ Please enter a number between 1 and 100.")
            except ValueError:
                print("  ❌ Please enter a valid number.")

        sample_size          = max(1, int(total_failed * (pct / 100)))
        est_tokens, est_cost = estimate_cost(sample_size)

        print("\n" + "-"*55)
        print(f"  Mode            : SAMPLE MODE ({pct}%)")
        print(f"  Jobs to analyse : {sample_size} of {total_failed}")
        print(f"  Est. tokens     : ~{est_tokens:,}")
        print(f"  Est. cost       : ~${est_cost:.4f}")
        print("-"*55)

        while True:
            confirm = input(
                "\n  Confirm and proceed? (y = proceed / n = go back to menu / q = quit): "
            ).strip().lower()

            if confirm == "y":
                return "sample", pct

            elif confirm == "n":
                print("\n  ↩️  Going back to analysis mode menu...\n")
                return show_analysis_menu(total_failed)

            elif confirm == "q":
                print("\n  ❌ Cancelled. Re-run to choose again.")
                return None, None

            else:
                print("  ❌ Invalid input. Please enter y, n, or q.")

    else:
        # ── Full Scan Mode ─────────────────────────────────────
        est_tokens, est_cost = estimate_cost(total_failed)

        print("\n" + "-"*55)
        print(f"  Mode            : FULL SCAN MODE")
        print(f"  Jobs to analyse : {total_failed} (all failures)")
        print(f"  Est. tokens     : ~{est_tokens:,}")
        print(f"  Est. cost       : ~${est_cost:.4f}")
        print("  ⚠️  Note: Large dataset may take 60-90 seconds")
        print("-"*55)

        while True:
            confirm = input(
                "\n  Confirm and proceed? (y = proceed / n = go back to menu / q = quit): "
            ).strip().lower()

            if confirm == "y":
                return "full", None

            elif confirm == "n":
                print("\n  ↩️  Going back to analysis mode menu...\n")
                return show_analysis_menu(total_failed)

            elif confirm == "q":
                print("\n  ❌ Cancelled. Re-run to choose again.")
                return None, None

            else:
                print("  ❌ Invalid input. Please enter y, n, or q.")


def build_gemini_prompt(failed_jobs, categorisation, total_jobs,
                        mode, sample_pct, jobs_to_analyse):
    """Build structured prompt for Gemini pattern analysis."""

    if mode == "full":
        analysis_note = f"FULL SCAN MODE — all {len(jobs_to_analyse)} failed jobs analysed"
    else:
        analysis_note = (f"SAMPLE MODE — {sample_pct}% sample "
                         f"({len(jobs_to_analyse)} of {len(failed_jobs)} failed jobs)")

    prompt = f"""
You are an expert Site Reliability Engineer (SRE) analysing data ingestion
pipeline failures for an enterprise financial services platform.

## Analysis Mode
{analysis_note}

## Overall Statistics
- Total jobs run: {total_jobs}
- Total failed jobs: {len(failed_jobs)}
- Overall failure rate: {(len(failed_jobs)/total_jobs)*100:.1f}%
- Jobs in this analysis: {len(jobs_to_analyse)}

## Failure Distribution (100% complete — all {len(failed_jobs)} failures)

By Component:
{json.dumps(categorisation['by_component'], indent=2)}

By Error Code:
{json.dumps(categorisation['by_error_code'], indent=2)}

By Failure Stage:
{json.dumps(categorisation['by_stage'], indent=2)}

By Severity:
{json.dumps(categorisation['by_severity'], indent=2)}

## Failed Jobs for Qualitative Analysis
{json.dumps(jobs_to_analyse, indent=2)}

## Your Task
Analyse the above failure data and provide:

1. PATTERN SUMMARY
   - What are the dominant failure patterns?
   - Are failures concentrated in specific components?
   - Is there a cascade effect (one failure causing others)?
   - Are specific pipelines disproportionately affected?

2. TOP 3 ROOT CAUSES
   - Identify the top 3 most likely root causes
   - Explain the evidence supporting each root cause
   - Rate confidence level (High/Medium/Low)

3. INCIDENT ASSESSMENT
   - Is this a major incident or isolated failures?
   - What is the estimated business impact?
   - Which pipelines are most affected?
   - What is the severity classification (P1/P2/P3)?

4. IMMEDIATE ACTIONS
   - List 3-5 immediate actions the SRE team should take
   - Prioritise by urgency (P1/P2/P3)
   - Include estimated resolution time for each action

Be specific, technical, and actionable. Reference actual error codes,
components, and pipeline names from the data provided.
"""
    return prompt


def run_detector(mode=None, sample_pct=None):
    """
    Main detector function.
    mode: 'sample' or 'full' (if None shows interactive menu)
    sample_pct: percentage of failures to sample (1-100)
    """
    print("\n" + "="*55)
    print("  AGENT 1 — FAILURE DETECTOR")
    print("="*55)

    # Step 1 — Load all logs
    all_jobs = load_all_logs()

    # Step 2 — Detect failures
    print("\n" + "-"*55)
    print("  STEP 1 — FAILURE DETECTION")
    print("-"*55)
    failed_jobs, completed_jobs = detect_failures(all_jobs)

    if not failed_jobs:
        print("\n  ✅ No failures detected. All jobs completed successfully.")
        return None

    # Step 3 — Categorise ALL failures (always 100% complete)
    print("\n" + "-"*55)
    print("  STEP 2 — FAILURE CATEGORISATION (100% of failures)")
    print("-"*55)
    categorisation = categorise_failures(failed_jobs)

    print("\n  By Component:")
    for component, count in sorted(categorisation["by_component"].items(),
                                   key=lambda x: x[1], reverse=True):
        pct = (count / len(failed_jobs)) * 100
        print(f"    {component:20} {count:5d} failures ({pct:.1f}%)")

    print("\n  By Failure Stage:")
    for stage, count in sorted(categorisation["by_stage"].items(),
                                key=lambda x: x[1], reverse=True):
        pct = (count / len(failed_jobs)) * 100
        print(f"    {stage:20} {count:5d} failures ({pct:.1f}%)")

    print("\n  By Severity:")
    for severity, count in sorted(categorisation["by_severity"].items(),
                                  key=lambda x: x[1], reverse=True):
        pct = (count / len(failed_jobs)) * 100
        print(f"    {severity:20} {count:5d} failures ({pct:.1f}%)")

    print("\n  Top 10 Error Codes:")
    top_errors = sorted(categorisation["by_error_code"].items(),
                        key=lambda x: x[1], reverse=True)[:10]
    for code, count in top_errors:
        pct = (count / len(failed_jobs)) * 100
        print(f"    {code:20} {count:5d} occurrences ({pct:.1f}%)")

    # Step 4 — Show analysis mode menu
    print("\n" + "-"*55)
    print("  STEP 3 — SELECT ANALYSIS MODE FOR GEMINI")
    print("-"*55)

    if mode is None:
        mode, sample_pct = show_analysis_menu(len(failed_jobs))
        if mode is None:
            return None

    # Step 5 — Select jobs for Gemini analysis
    if mode == "full":
        jobs_to_analyse = failed_jobs
    else:
        sample_size     = max(1, int(len(failed_jobs) * (sample_pct / 100)))
        jobs_to_analyse = failed_jobs[:sample_size]

    # Step 6 — Run Gemini analysis
    print("\n" + "-"*55)
    print("  STEP 4 — GEMINI PATTERN ANALYSIS")
    print("-"*55)
    print(f"  Mode      : {'FULL SCAN' if mode == 'full' else f'SAMPLE ({sample_pct}%)'}")
    print(f"  Analysing : {len(jobs_to_analyse)} of {len(failed_jobs)} failed jobs")
    print(f"  Sending to Gemini...")

    prompt = build_gemini_prompt(
        failed_jobs, categorisation, len(all_jobs),
        mode, sample_pct, jobs_to_analyse
    )
    response        = client.models.generate_content(model=MODEL, contents=prompt)
    gemini_analysis = response.text
    print("  ✅ Gemini analysis complete")

    # Step 7 — Build output for Agent 2
    detection_output = {
        "scan_timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analysis_mode":    mode,
        "sample_pct":       sample_pct if mode == "sample" else 100,
        "total_jobs":       len(all_jobs),
        "total_completed":  len(completed_jobs),
        "total_failed":     len(failed_jobs),
        "failure_rate_pct": round((len(failed_jobs)/len(all_jobs))*100, 1),
        "jobs_analysed":    len(jobs_to_analyse),
        "categorisation":   categorisation,
        "failed_jobs":      failed_jobs,
        "jobs_to_analyse":  jobs_to_analyse,
        "gemini_analysis":  gemini_analysis
    }

    print("\n" + "="*55)
    print("  AGENT 1 COMPLETE")
    print("="*55)
    print(f"  Total failures identified : {len(failed_jobs)}")
    print(f"  Jobs analysed by Gemini   : {len(jobs_to_analyse)}")
    print(f"  Analysis mode             : {'FULL SCAN' if mode == 'full' else f'SAMPLE ({sample_pct}%)'}")
    print(f"  Passing to Agent 2 for RCA...")
    print("="*55 + "\n")

    return detection_output


if __name__ == "__main__":
    result = run_detector()
    if result:
        print("\n  GEMINI PATTERN ANALYSIS:")
        print("  " + "-"*51)
        print(result["gemini_analysis"])
