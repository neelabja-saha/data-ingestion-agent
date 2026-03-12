import json
import os
import random
import uuid
from datetime import datetime, timedelta

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.dirname(__file__))
ERROR_CODES_PATH = os.path.join(BASE_DIR, "data", "error_codes.json")
LOGS_DIR        = os.path.join(BASE_DIR, "data", "logs")

# ── Simulation config ──────────────────────────────────────────────────────
HOURS           = 6
JOBS_PER_HOUR   = 800
SIM_START       = datetime(2026, 3, 12, 0, 0, 0)   # simulation start time

# ── Pipeline metadata pools ────────────────────────────────────────────────
PIPELINE_NAMES = [
    "customer_transactions_to_bigquery",
    "merchant_data_to_bigquery",
    "fraud_signals_to_bigquery",
    "loyalty_points_to_bigquery",
    "card_applications_to_bigquery",
    "credit_limits_to_bigquery",
    "dispute_records_to_bigquery",
    "settlement_data_to_bigquery",
    "risk_scores_to_bigquery",
    "account_updates_to_bigquery",
]

SOURCES = [
    "Oracle_DB", "MySQL_DB", "PostgreSQL_DB",
    "Salesforce_API", "SAP_ERP", "REST_API",
    "Kafka_Stream", "S3_Bucket", "SFTP_Server", "MongoDB"
]

TARGET = "BigQuery"

# ── Status trail timing (seconds between each status transition) ───────────
STATUS_TIMING = {
    "ACKNOWLEDGED": 0,
    "WAITING":      random.randint(2, 8),
    "QUEUED":       random.randint(5, 20),
    "IN_PROGRESS":  random.randint(30, 300),
}

# Stages at which a job can fail
FAILURE_STAGES = ["WAITING", "QUEUED", "IN_PROGRESS"]

# Failure stage → likely error code prefixes
STAGE_ERROR_MAP = {
    "WAITING":     ["VAL"],
    "QUEUED":      ["ORC"],
    "IN_PROGRESS": ["EXT", "TRF", "LOD", "PLT", "ADH"],
}

def load_error_codes():
    """Load error codes dictionary."""
    with open(ERROR_CODES_PATH, "r") as f:
        return json.load(f)

def get_failure_count():
    """
    Return a random failure count between 0 and 800 with good variance.
    Uses a mix of low, medium and high failure hours to create realistic patterns.
    """
    roll = random.random()
    if roll < 0.15:
        # Very low failure hour (0–5%)
        return random.randint(0, int(JOBS_PER_HOUR * 0.05))
    elif roll < 0.40:
        # Low failure hour (5–15%)
        return random.randint(int(JOBS_PER_HOUR * 0.05), int(JOBS_PER_HOUR * 0.15))
    elif roll < 0.70:
        # Medium failure hour (15–30%)
        return random.randint(int(JOBS_PER_HOUR * 0.15), int(JOBS_PER_HOUR * 0.30))
    elif roll < 0.90:
        # High failure hour (30–60%)
        return random.randint(int(JOBS_PER_HOUR * 0.30), int(JOBS_PER_HOUR * 0.60))
    else:
        # Incident hour (60–100%)
        return random.randint(int(JOBS_PER_HOUR * 0.60), JOBS_PER_HOUR)

def build_status_trail(start_time, final_status, failure_stage=None):
    """
    Build a realistic status trail for a job.
    Returns list of status events with timestamps.
    """
    trail = []
    current_time = start_time

    statuses = ["ACKNOWLEDGED", "WAITING", "QUEUED", "IN_PROGRESS"]

    for status in statuses:
        trail.append({
            "status": status,
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        # Advance time
        if status == "ACKNOWLEDGED":
            current_time += timedelta(seconds=random.randint(2, 8))
        elif status == "WAITING":
            current_time += timedelta(seconds=random.randint(5, 20))
        elif status == "QUEUED":
            current_time += timedelta(seconds=random.randint(10, 60))
        elif status == "IN_PROGRESS":
            current_time += timedelta(seconds=random.randint(30, 600))

        # If this is where the job fails, stop here
        if final_status == "FAILED" and status == failure_stage:
            trail.append({
                "status": "FAILED",
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
            })
            return trail, current_time

    # Job completed successfully
    trail.append({
        "status": "COMPLETED",
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
    })
    return trail, current_time

def pick_error_for_stage(stage, error_codes):
    """Pick a realistic error code based on failure stage."""
    prefixes = STAGE_ERROR_MAP[stage]
    matching_codes = [
        code for code in error_codes.keys()
        if any(code.startswith(prefix) for prefix in prefixes)
    ]
    chosen_code = random.choice(matching_codes)
    entry = error_codes[chosen_code]
    scenario = random.choice(entry["failure_scenarios"])
    return {
        "component":      entry["component"],
        "error_code":     entry["error_code"],
        "error_message":  entry["error_message"],
        "severity":       entry["severity"],
        "scenario_id":    scenario["scenario_id"],
        "scenario":       scenario["scenario"],
        "trigger":        scenario["trigger"],
        "error_log_url":  entry["error_log_url_template"].replace("{job_id}", "JOB_PLACEHOLDER")
    }

def generate_job(job_id, start_time, is_failed, failure_stage, error_codes):
    """Generate a single ingestion job log."""
    pipeline = random.choice(PIPELINE_NAMES)
    source   = random.choice(SOURCES)

    if is_failed:
        status_trail, end_time = build_status_trail(start_time, "FAILED", failure_stage)
        error_detail = pick_error_for_stage(failure_stage, error_codes)
        error_detail["error_log_url"] = error_detail["error_log_url"].replace(
            "JOB_PLACEHOLDER", job_id
        )
        final_status = "FAILED"
    else:
        status_trail, end_time = build_status_trail(start_time, "COMPLETED")
        error_detail = None
        final_status = "COMPLETED"

    job = {
        "job_id":        job_id,
        "pipeline_name": pipeline,
        "source":        source,
        "target":        TARGET,
        "start_time":    start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time":      end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "final_status":  final_status,
        "status_trail":  status_trail,
        "error":         error_detail
    }
    return job

def generate_logs():
    """Main function — generates all logs for 6 hours."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    error_codes = load_error_codes()

    total_jobs      = 0
    total_failed    = 0
    total_completed = 0

    print("\n" + "="*55)
    print("  DATA INGESTION LOG GENERATOR")
    print("="*55)
    print(f"  Simulation period : {HOURS} hours")
    print(f"  Jobs per hour     : {JOBS_PER_HOUR}")
    print(f"  Total jobs        : {HOURS * JOBS_PER_HOUR}")
    print(f"  Output directory  : {LOGS_DIR}")
    print("="*55 + "\n")

    for hour in range(1, HOURS + 1):
        hour_start  = SIM_START + timedelta(hours=hour - 1)
        failure_count = get_failure_count()
        jobs_this_hour = []

        # Decide which job indices will fail this hour
        failed_indices = set(random.sample(range(JOBS_PER_HOUR), min(failure_count, JOBS_PER_HOUR)))

        for i in range(JOBS_PER_HOUR):
            # Spread jobs evenly across the hour
            job_offset = timedelta(seconds=(3600 / JOBS_PER_HOUR) * i)
            job_start  = hour_start + job_offset
            job_id     = f"JOB_{hour_start.strftime('%Y%m%d')}_{hour:02d}_{i+1:04d}"

            is_failed = i in failed_indices
            if is_failed:
                failure_stage = random.choice(FAILURE_STAGES)
            else:
                failure_stage = None

            job = generate_job(job_id, job_start, is_failed, failure_stage, error_codes)
            jobs_this_hour.append(job)

        # Save hour log file
        hour_file = os.path.join(LOGS_DIR, f"logs_hour_{hour:02d}.json")
        with open(hour_file, "w") as f:
            json.dump(jobs_this_hour, f, indent=2)

        hour_failed    = sum(1 for j in jobs_this_hour if j["final_status"] == "FAILED")
        hour_completed = JOBS_PER_HOUR - hour_failed
        total_jobs      += JOBS_PER_HOUR
        total_failed    += hour_failed
        total_completed += hour_completed

        print(f"  Hour {hour:02d} | Jobs: {JOBS_PER_HOUR} | "
              f"Completed: {hour_completed:4d} | "
              f"Failed: {hour_failed:4d} | "
              f"Failure rate: {(hour_failed/JOBS_PER_HOUR)*100:.1f}%")

    print("\n" + "="*55)
    print("  GENERATION COMPLETE")
    print("="*55)
    print(f"  Total jobs      : {total_jobs}")
    print(f"  Total completed : {total_completed} ({(total_completed/total_jobs)*100:.1f}%)")
    print(f"  Total failed    : {total_failed} ({(total_failed/total_jobs)*100:.1f}%)")
    print(f"  Log files saved : {LOGS_DIR}")
    print("="*55 + "\n")

if __name__ == "__main__":
    generate_logs()