import json
import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# ── Load environment variables ─────────────────────────────────────────────
load_dotenv()

# ── Gemini client ──────────────────────────────────────────────────────────
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def build_component_rca_prompt(component, component_jobs, total_failed):
    """
    Build a focused RCA prompt for a single component.
    """
    # Get error code distribution for this component
    error_code_counts = {}
    for job in component_jobs:
        error = job.get("error", {})
        code  = error.get("error_code", "Unknown")
        error_code_counts[code] = error_code_counts.get(code, 0) + 1

    top_errors = sorted(error_code_counts.items(), key=lambda x: x[1], reverse=True)

    # Get failure stage distribution
    stage_counts = {}
    for job in component_jobs:
        trail = job.get("status_trail", [])
        for i, entry in enumerate(trail):
            if entry["status"] == "FAILED" and i > 0:
                stage = trail[i-1]["status"]
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
                break

    # Get unique scenarios
    scenarios = []
    seen = set()
    for job in component_jobs:
        error = job.get("error", {})
        scenario_id = error.get("scenario_id", "")
        if scenario_id and scenario_id not in seen:
            seen.add(scenario_id)
            scenarios.append({
                "scenario_id": scenario_id,
                "scenario":    error.get("scenario", ""),
                "trigger":     error.get("trigger", "")
            })

    prompt = f"""
You are an expert Site Reliability Engineer (SRE) performing a Root Cause Analysis
for an enterprise financial services data ingestion platform.

## Component Under Analysis
Component: {component}
Total failures in this component: {len(component_jobs)}
As % of all failures: {(len(component_jobs)/total_failed)*100:.1f}%

## Error Code Distribution
{json.dumps(dict(top_errors), indent=2)}

## Failure Stage Distribution
{json.dumps(stage_counts, indent=2)}

## Unique Failure Scenarios Observed
{json.dumps(scenarios, indent=2)}

## Sample Failed Jobs (up to 20)
{json.dumps(component_jobs[:20], indent=2)}

## Your Task
Provide a focused Root Cause Analysis for the {component} component only.

1. PRIMARY ROOT CAUSE
   - What is the single most likely root cause for these failures?
   - What specific evidence from the data supports this?
   - Confidence level: High / Medium / Low

2. CONTRIBUTING FACTORS
   - List 2-3 contributing factors that amplified the failures
   - Be specific to the error codes and scenarios observed

3. BUSINESS IMPACT
   - What is the specific business impact of this component failing?
   - Which downstream processes or business functions are affected?

4. RECOMMENDED FIXES
   - List exactly 3 fixes in priority order (Fix 1, Fix 2, Fix 3)
   - For each fix: what to do, how long it will take, who owns it
   - Fix 1 should be immediately actionable (within 2 hours)
   - Fix 2 should be short-term (within 24 hours)
   - Fix 3 should be long-term (within 1 week)

Keep your response concise, specific, and actionable.
Reference actual error codes and scenario IDs from the data.
"""
    return prompt


def perform_component_rca(failed_jobs, jobs_to_analyse, categorisation):
    """
    Perform per-component RCA using Gemini.
    Uses jobs_to_analyse (respects Agent 1 mode choice).
    """
    total_failed   = len(failed_jobs)
    component_rca  = {}
    components     = sorted(
        categorisation["by_component"].items(),
        key=lambda x: x[1], reverse=True
    )

    print(f"\n  Running per-component RCA for {len(components)} components...")
    print(f"  Using {len(jobs_to_analyse)} jobs (respecting Agent 1 mode choice)\n")

    for component, count in components:
        # Filter jobs_to_analyse for this component
        component_jobs = [
            j for j in jobs_to_analyse
            if j.get("error", {}).get("component") == component
        ]

        if not component_jobs:
            print(f"  ⚠️  {component:20} — no jobs in analysed set, skipping Gemini call")
            component_rca[component] = {
                "failure_count":     count,
                "pct_of_failures":   round((count / total_failed) * 100, 1),
                "jobs_in_analysis":  0,
                "top_error_codes":   [],
                "gemini_rca":        "Insufficient data in sample for detailed RCA. Run in Full Scan mode for complete analysis."
            }
            continue

        print(f"  🔍 Analysing {component:20} — {len(component_jobs):4d} jobs in analysis set...")

        # Get top error codes for this component
        error_code_counts = {}
        for job in component_jobs:
            code = job.get("error", {}).get("error_code", "Unknown")
            error_code_counts[code] = error_code_counts.get(code, 0) + 1
        top_errors = sorted(error_code_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Call Gemini for this component
        prompt   = build_component_rca_prompt(component, component_jobs, total_failed)
        response = client.models.generate_content(model=MODEL, contents=prompt)

        component_rca[component] = {
            "failure_count":     count,
            "pct_of_failures":   round((count / total_failed) * 100, 1),
            "jobs_in_analysis":  len(component_jobs),
            "top_error_codes":   top_errors,
            "gemini_rca":        response.text
        }
        print(f"  ✅ {component:20} — RCA complete")

    return component_rca


def calculate_pipeline_impact(failed_jobs, jobs_to_analyse):
    """
    Calculate per-pipeline failure statistics.
    Pure Python — no Gemini call needed.
    """
    # Count total jobs per pipeline from jobs_to_analyse
    pipeline_failures  = {}
    pipeline_components = {}

    for job in jobs_to_analyse:
        pipeline = job.get("pipeline_name", "Unknown")
        component = job.get("error", {}).get("component", "Unknown")

        pipeline_failures[pipeline] = pipeline_failures.get(pipeline, 0) + 1

        if pipeline not in pipeline_components:
            pipeline_components[pipeline] = {}
        pipeline_components[pipeline][component] = (
            pipeline_components[pipeline].get(component, 0) + 1
        )

    # Build pipeline impact list sorted by failure count
    pipeline_impact = []
    for pipeline, failures in sorted(pipeline_failures.items(),
                                      key=lambda x: x[1], reverse=True):
        pipeline_impact.append({
            "pipeline":          pipeline,
            "failure_count":     failures,
            "components_affected": pipeline_components[pipeline]
        })

    return pipeline_impact


def extract_action_items(gemini_analysis):
    """
    Ask Gemini to extract and structure action items
    from Agent 1's pattern analysis into a clean table format.
    """
    prompt = f"""
From the following SRE incident analysis, extract all action items and
format them as a structured JSON list.

Analysis:
{gemini_analysis}

Return ONLY a JSON array with no markdown formatting, no code blocks,
no preamble. Each item must have exactly these fields:
- priority: "P1", "P2", or "P3"
- action: short action title (max 10 words)
- description: what needs to be done (max 30 words)
- owner: who should own this (e.g. "SRE Team", "Data Engineering", "Platform Team")
- estimated_time: how long it will take (e.g. "30 minutes", "2 hours", "1 day")

Example format:
[
  {{
    "priority": "P1",
    "action": "Establish incident war room",
    "description": "Convene cross-functional team of SRE, Data Engineering and business stakeholders",
    "owner": "SRE Team",
    "estimated_time": "30 minutes"
  }}
]
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    raw      = response.text.strip()

    # Clean up response in case Gemini adds markdown
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        action_items = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if parsing fails
        action_items = [{
            "priority":       "P1",
            "action":         "Review full Gemini analysis",
            "description":    "See Pattern Analysis section for detailed action items",
            "owner":          "SRE Team",
            "estimated_time": "Immediate"
        }]

    return action_items


def run_reporter(detection_output):
    """
    Main reporter function.
    Receives detection_output from Agent 1 and builds full report.
    """
    print("\n" + "="*55)
    print("  AGENT 2 — RCA REPORTER")
    print("="*55)
    print(f"  Received from Agent 1:")
    print(f"    Total failures    : {detection_output['total_failed']}")
    print(f"    Analysis mode     : {detection_output['analysis_mode'].upper()}")
    print(f"    Jobs to analyse   : {detection_output['jobs_analysed']}")

    failed_jobs     = detection_output["failed_jobs"]
    jobs_to_analyse = detection_output["jobs_to_analyse"]
    categorisation  = detection_output["categorisation"]
    gemini_analysis = detection_output["gemini_analysis"]

    # Step 1 — Per-component RCA
    print("\n" + "-"*55)
    print("  STEP 1 — PER-COMPONENT RCA")
    print("-"*55)
    component_rca = perform_component_rca(
        failed_jobs, jobs_to_analyse, categorisation
    )

    # Step 2 — Pipeline impact
    print("\n" + "-"*55)
    print("  STEP 2 — PIPELINE IMPACT ASSESSMENT")
    print("-"*55)
    pipeline_impact = calculate_pipeline_impact(failed_jobs, jobs_to_analyse)
    print(f"\n  Pipeline failure ranking:")
    for i, p in enumerate(pipeline_impact, 1):
        print(f"    {i:2d}. {p['pipeline']:45} {p['failure_count']:4d} failures")

    # Step 3 — Extract action items
    print("\n" + "-"*55)
    print("  STEP 3 — EXTRACTING ACTION ITEMS")
    print("-"*55)
    print("  Asking Gemini to structure action items...")
    action_items = extract_action_items(gemini_analysis)
    print(f"  ✅ {len(action_items)} action items extracted")

    # Step 4 — Build complete report structure
    print("\n" + "-"*55)
    print("  STEP 4 — BUILDING REPORT STRUCTURE")
    print("-"*55)

    report = {
        "metadata": {
            "generated_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analysis_mode":   detection_output["analysis_mode"].upper(),
            "sample_pct":      detection_output["sample_pct"],
            "scan_timestamp":  detection_output["scan_timestamp"],
            "period_start":    "2026-03-11 00:00:00",
            "period_end":      "2026-03-11 05:59:59",
        },
        "executive_summary": {
            "total_jobs":        detection_output["total_jobs"],
            "total_completed":   detection_output["total_completed"],
            "total_failed":      detection_output["total_failed"],
            "failure_rate_pct":  detection_output["failure_rate_pct"],
            "jobs_analysed":     detection_output["jobs_analysed"],
            "incident_level":    "P1 - Critical",
            "severity_breakdown": categorisation["by_severity"],
            "stage_breakdown":   categorisation["by_stage"],
            "component_breakdown": categorisation["by_component"],
        },
        "pattern_analysis":  gemini_analysis,
        "component_rca":     component_rca,
        "pipeline_impact":   pipeline_impact,
        "action_items":      action_items,
        "top_error_codes":   sorted(
            categorisation["by_error_code"].items(),
            key=lambda x: x[1], reverse=True
        )[:10]
    }

    print("  ✅ Report structure complete")

    print("\n" + "="*55)
    print("  AGENT 2 COMPLETE")
    print("="*55)
    print(f"  Components analysed : {len(component_rca)}")
    print(f"  Pipelines assessed  : {len(pipeline_impact)}")
    print(f"  Action items        : {len(action_items)}")
    print(f"  Passing to PDF generator...")
    print("="*55 + "\n")

    return report


if __name__ == "__main__":
    # For standalone testing — loads a sample detection output
    print("\n  ⚠️  Agent 2 is designed to be called from main.py")
    print("  Run main.py to execute the full pipeline.\n")
