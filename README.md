# Data Ingestion Anomaly Agent

An agentic AI system that monitors data pipeline failures, detects anomalies, performs root cause analysis using an LLM, and generates a structured incident report as a PDF — automatically.

Built as a portfolio project by a Senior Product Manager to demonstrate hands-on agentic AI development in an enterprise data platform context.

---

## The Problem

In large-scale data platforms, pipelines fail constantly. An enterprise ingestion platform running 800+ jobs per hour can generate thousands of failures across a 6-hour window. Today, on-call engineers:

- Manually triage logs to identify which components are failing
- Spend 30–60 minutes per incident piecing together root cause
- Produce incident reports manually after the fact
- Have no consistent format for escalation to leadership

This tool automates that entire workflow — from raw logs to a structured PDF report — in under 2 minutes.

---

## How It Works

The system uses a two-agent pipeline orchestrated by `main.py`:

```
Raw Log Files (JSON)
        │
        ▼
┌─────────────────────┐
│     Agent 1         │
│  Failure Detector   │  ◄── Loads all log files, detects failures,
│                     │       categorises by component & error code,
│  Sample or Full     │       sends to Gemini for pattern analysis
│  Scan toggle        │
└────────┬────────────┘
         │  detection_output{}
         ▼
┌─────────────────────┐
│     Agent 2         │
│   RCA Reporter      │  ◄── Per-component root cause analysis,
│                     │       pipeline impact ranking,
│  7 Gemini calls     │       action items (P1 / P2 / P3)
└────────┬────────────┘
         │  report{}
         ▼
┌─────────────────────┐
│   PDF Generator     │  ◄── Builds 6-page structured incident report
│                     │       saved to reports/ with timestamp
└─────────────────────┘
         │
         ▼
  rca_report_YYYYMMDD_HHMMSS.pdf
```

**Total Gemini API calls per run: 9**
- 1 call — pattern analysis (Agent 1)
- 7 calls — per-component RCA (Agent 2)
- 1 call — action items extraction (Agent 2)

---

## Report Output

The generated PDF contains 6 sections:

| Section | Contents |
|---|---|
| Cover | Incident severity badge, report metadata, timestamp |
| Executive Summary | KPI boxes, severity breakdown table, top 10 error codes |
| LLM Pattern Analysis | Horizontal bar chart by component + Gemini narrative |
| Component RCA | Per-component deep dive with root cause and fixes |
| Pipeline Impact | Ranked table of most affected pipelines |
| Action Items | P1 / P2 / P3 prioritised actions with owner and timeframe |

---

## Agent 1 — Analysis Modes

At runtime, the user selects one of two modes:

| Mode | Description | When to use |
|---|---|---|
| **Sample Mode** | Analyse a user-defined % of failures | Exploratory runs, cost-sensitive environments |
| **Full Scan Mode** | Analyse all failed jobs | Production incidents, enterprise platforms |

Failure categorisation always runs on 100% of failures regardless of mode. Only the Gemini analysis step is scoped by the toggle.

Cost estimate is shown before confirmation. User can proceed, go back to menu, or quit.

---

## Tech Stack

| Area | Technology |
|---|---|
| Language | Python 3.11 |
| LLM | Google Gemini 2.5 Flash via `google-genai` |
| PDF Generation | ReportLab |
| Environment | `python-dotenv` |
| Platform | GCP-aligned (BigQuery, Airflow context) |

---

## Project Structure

```
data-ingestion-agent/
├── data/
│   ├── error_codes.json          # 21 error codes, 210 failure scenarios
│   └── logs/                     # Generated log files (git-ignored)
├── docs/
│   └── PM_RETROSPECTIVE.md       # Product decisions and trade-offs log
├── reports/                      # Generated PDF reports (git-ignored)
├── src/
│   ├── log_generator.py          # Simulates 4,800 pipeline jobs across 6 hours
│   ├── agent1_detector_with_toggle.py  # Failure detection + Gemini pattern analysis
│   ├── agent2_reporter.py        # Per-component RCA + action items
│   └── pdf_generator.py          # 6-page PDF report builder
├── main.py                       # Orchestrator — runs full pipeline end to end
├── lookup.py                     # Error code lookup utility
├── .env.example                  # Environment variable template
├── .gitignore
└── requirements.txt
```

---

## Setup & Run

**1. Clone the repository**
```bash
git clone https://github.com/neelabja-saha/data-ingestion-agent.git
cd data-ingestion-agent
```

**2. Create and activate virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

Copy `.env.example` to `.env` and add your Gemini API key:
```
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
Get a free API key at [aistudio.google.com](https://aistudio.google.com)

**5. Generate simulation logs**
```bash
python src/log_generator.py
```

**6. Run the full agent pipeline**
```bash
python main.py
```

The PDF report will be saved to `reports/rca_report_YYYYMMDD_HHMMSS.pdf`

---

## V1 Features

- Simulated log generator — 4,800 jobs across 6 hours with realistic failure variance
- 21 error codes across 7 pipeline components (Extractor, Transformer, Validator, Loader, Orchestrator, Platform, Adhoc)
- 210 failure scenarios with root cause triggers
- Sample Mode vs Full Scan Mode toggle with cost estimate
- Two-agent pipeline with 9 Gemini API calls
- 6-page structured PDF incident report
- P1 / P2 / P3 prioritised action items

---

## V2 Roadmap

| Feature | Description | Priority |
|---|---|---|
| Report type toggle | Executive summary report vs full RCA report | High |
| Job ID mode | Targeted RCA on specific job IDs by input | High |
| Minimum sample size warning | Warn user if sample % produces incomplete component coverage | Medium |
| Mode audit trail | Log report type and analysis mode in PDF footer | Medium |

See [`docs/PM_RETROSPECTIVE.md`](docs/PM_RETROSPECTIVE.md) for full product decision log including rationale and trade-offs for each v2 enhancement.

---

## About This Project

This project was built to demonstrate that a Senior PM can go beyond spec-writing and build functional agentic AI systems end to end — including architecture decisions, prompt engineering, agent orchestration, and output design.

Every repo in this portfolio includes a PM Retrospective documenting product decisions, trade-offs, and what would be done differently — because shipping is only half the job.

The output of this agent is used as the evaluation target for [`hallucination-auditor-agent`](https://github.com/neelabja-saha/hallucination-auditor-agent) — a meta-agent system that audits, scores, and self-improves agentic pipelines.

**Author:** Neelabja Saha — [LinkedIn](https://www.linkedin.com/in/neelabja-saha) · [GitHub](https://github.com/neelabja-saha)
