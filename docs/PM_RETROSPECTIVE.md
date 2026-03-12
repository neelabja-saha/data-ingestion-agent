# PM Retrospective — Data Ingestion Anomaly Agent

**Project:** `data-ingestion-agent`  
**Version:** 1.0.0  
**Period:** March 2026  
**Author:** Neelabja Saha

This document captures product decisions, trade-offs, and future enhancement ideas made during the design and build of v1. It is written from a PM perspective — not just what was built, but why, and what would be done differently or next.

---

## Entry 1 — Sampling vs Full Scan Decision

**Context:**
Agent 1 needed to decide how many failed jobs to send to Gemini for pattern analysis. Sending all failures is expensive; sending a sample risks missing components entirely.

**Decision:**
A toggle system was introduced giving the user two modes at runtime:
- **Sample Mode** — user defines a percentage of failed jobs to analyse
- **Full Scan Mode** — all failed jobs sent to Gemini for analysis

Categorisation (grouping failures by component and error code) runs on 100% of failures regardless of which mode is chosen. Only the Gemini analysis step is scoped by the toggle.

**Rationale:**
Cost difference between modes is minimal (~$0.003 sample vs ~$0.10 full scan) but the coverage risk is significant. A 10% sample on 1,700 failures could leave entire components with zero jobs in scope, producing incomplete RCA. For an enterprise financial platform, incomplete RCA is worse than no RCA.

**Outcome:**
Full Scan is recommended as the default for production use. Sample Mode retained for cost-sensitive or exploratory runs.

**Future Enhancements:**
- Auto-recommend Full Scan when Critical severity failures exceed a configurable threshold
- Add cost preview before user confirms mode selection
- Log selected mode in the PDF footer for audit trail purposes

---

## Entry 2 — Agent 2 Respecting Agent 1 Mode Choice

**Context:**
After Agent 1 completes detection and mode selection, Agent 2 needed to decide whether to ask the user again which jobs to analyse, or inherit the decision from Agent 1.

**Decision:**
Agent 2 reads `jobs_to_analyse` directly from `detection_output` — the dictionary passed from Agent 1. No new user prompt is introduced at Agent 2 entry.

**Rationale:**
`jobs_to_analyse` becomes the single source of truth for job scope across the entire pipeline. Asking the user again at Agent 2 would create inconsistency — the pattern analysis and the RCA could end up covering different job sets, making the report contradictory and untrustworthy.

**Outcome:**
Same job set used for Gemini pattern analysis, per-component RCA, pipeline impact ranking, and action items. Report is internally consistent end to end.

---

## Entry 3 — Minimum Sample Size Warning (Future Enhancement)

**Context:**
In Sample Mode, if a user selects a very low percentage (e.g. 5%), some components may have zero jobs in the sample. Agent 2 currently skips Gemini for those components and flags a warning in the report.

**Current Behaviour:**
If a component has 0 jobs in the sample, Agent 2 skips the Gemini RCA call for that component and adds a warning message to the report section.

**Gap Identified:**
The user is not warned at the point of choosing their sample percentage — they only discover the gap after the report is generated. This is poor UX for a tool used in incident response where time matters.

**Future Enhancement:**
- After the user enters a sample percentage, calculate the expected average jobs per component
- If any component is projected to have fewer than ~10 jobs, show a warning before confirming
- Suggest a minimum percentage that ensures full component coverage
- Priority: Medium — acceptable for v1, target for v2

---

## Entry 4 — PDF Formatting Decisions

**Context:**
The PDF generator went through multiple iterations to resolve layout, readability, and formatting issues with ReportLab.

**Key Decisions and Lessons:**

**Nested tables removed for text content**
ReportLab nested tables overflow unpredictably when text content is long. All text sections moved to plain `Paragraph` flowables with controlled styles.

**Gemini markdown parsed line by line**
Gemini responses contain markdown (`**bold**`, `- bullets`). These were parsed line by line into individual ReportLab `Paragraph` objects rather than passed as raw strings — raw strings render markdown syntax literally rather than formatting it.

**Action items priority header**
The P1/P2/P3 priority label was merged as Row 0 of the action items table using a SPAN across all columns. This ensures the header is visually aligned with the table body and does not float independently.

**Bar chart percentage labels**
Percentage added inside the horizontal bars on the pattern analysis chart with white text. Count shown to the right of each bar. Improves at-a-glance readability without requiring the reader to calculate proportions.

**Cover page text colour**
All cover page text explicitly set to white. ReportLab does not inherit text colour from the canvas background — without explicit colour assignment, text rendered as black on a navy background and was invisible.

**Section heading bars**
Section heading background colour fixed by wrapping all 5 section titles in a `Table` with `colWidths=[CONTENT_WIDTH]`. `ParagraphStyle backColor` only fills colour behind the text characters themselves — it does not stretch to full page width. The Table wrapper guarantees edge-to-edge navy bars matching the width of all other tables and charts.

**Model-agnostic naming**
Section renamed from "Gemini Pattern Analysis" to "LLM Pattern Analysis". Production reports should not expose the underlying model provider — this makes the output portable if the model is swapped in future versions.

---

## Entry 5 — Report Type Toggle & Job-Specific RCA (Planned for v2)

**Context:**
V1 always generates one report format — the full in-depth RCA report. Two enhancement requests identified after v1 completion that would significantly expand the tool's usefulness across different user personas.

---

**Enhancement 1: Report Type Toggle**

**Problem:**
The full RCA report is designed for SRE and engineering teams. Leadership and stakeholders need a shorter, higher-level view — they do not need per-component deep dives, they need severity summary, top errors, and prioritised actions.

**Decision:**
Add a report type selection step in `main.py` between Agent 2 completing and PDF generation starting. Two modes:

- **Executive Report** — cover page, KPI summary, severity breakdown, top errors, bar chart, prioritised action items only. No per-component RCA detail. Designed for VPs, Directors, and stakeholders
- **Full RCA Report** — current v1 behaviour. All sections including per-component deep dive, pipeline impact ranking, and recommended fixes. Designed for SRE and engineering teams

Both report types use the same `report` dictionary produced by Agent 2. The `pdf_generator.py` conditionally includes or excludes sections based on the selected mode — no duplicate data processing.

Report type logged in PDF metadata and footer for audit trail.

---

**Enhancement 2: Job-Specific RCA by Job ID**

**Problem:**
Current pipeline analyses all failed jobs or a sample percentage. On-call engineers responding to a specific production alert need targeted RCA on one or a few known job IDs — not a full pipeline scan.

**Decision:**
Add a third input mode to Agent 1 — Job ID Mode. User enters one or more Job IDs manually (comma-separated). Agent 1 extracts only those jobs from the log files, validates they exist, and flags any IDs not found.

Agent 2 runs focused per-job RCA — each job gets its own root cause narrative instead of component-level aggregation. PDF gets a dedicated `Job-Specific RCA` section replacing the component RCA section when this mode is active.

**Use case:**
On-call engineer sees `JOB_20260311_03_0412` fail in a production alert. Runs the tool with that job ID. Gets a targeted RCA report in under 2 minutes without triggering a full pipeline scan.

---

**Refactoring Plan for v2:**

| File | Change |
|---|---|
| `agent1_detector_with_toggle.py` | Add Job ID Mode as third menu option; validate and extract requested jobs; return mode flag in `detection_output` |
| `agent2_reporter.py` | Branch logic on `detection_output['mode']`; if Job ID mode, run per-job Gemini RCA instead of per-component aggregation |
| `pdf_generator.py` | Add `build_executive_report()` as lightweight alternative to full build; add `build_job_specific_rca()` section for Job ID mode |
| `main.py` | Add report type selection menu after Agent 2 completes; pass selection into `generate_pdf()` |

All changes refactored into existing files — no new files, no parallel pipelines.

---

## Summary — V1 Decisions vs V2 Targets

| Decision Area | V1 Behaviour | V2 Target |
|---|---|---|
| Analysis scope | Sample % or Full Scan | + Job ID Mode |
| Report format | Full RCA only | + Executive Report toggle |
| Sample size warning | Silent skip with report flag | Proactive warning at input stage |
| Mode audit trail | Not logged | Report type logged in PDF footer |
| Model naming | Fixed to Gemini | Model-agnostic throughout |
