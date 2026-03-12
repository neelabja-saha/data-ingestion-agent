import json
import os

error_codes = {
  "EXT_001": {
    "component": "Extractor",
    "error_code": "EXT_001",
    "error_message": "Source system unavailable",
    "severity": "Critical",
    "description": "The source system could not be reached during extraction",
    "recommended_action": "Check source system availability and network connectivity",
    "error_log_url_template": "https://logs.platform.com/errors/EXT_001/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "EXT_001_S1", "scenario": "Source database server is down", "trigger": "Scheduled maintenance or unplanned outage"},
      {"scenario_id": "EXT_001_S2", "scenario": "Source API endpoint is unreachable", "trigger": "Network routing issue or firewall rule change"},
      {"scenario_id": "EXT_001_S3", "scenario": "Source system overloaded and rejecting connections", "trigger": "High traffic volume on source system"},
      {"scenario_id": "EXT_001_S4", "scenario": "DNS resolution failure for source host", "trigger": "DNS configuration change or propagation delay"},
      {"scenario_id": "EXT_001_S5", "scenario": "Source system SSL certificate expired", "trigger": "Certificate renewal missed or delayed"},
      {"scenario_id": "EXT_001_S6", "scenario": "Source system port blocked by security policy", "trigger": "Recent security policy update blocking outbound connections"},
      {"scenario_id": "EXT_001_S7", "scenario": "Source system IP address changed without pipeline config update", "trigger": "Infrastructure migration or IP reallocation"},
      {"scenario_id": "EXT_001_S8", "scenario": "VPN tunnel to source system dropped", "trigger": "VPN session timeout or credential expiry"},
      {"scenario_id": "EXT_001_S9", "scenario": "Source system undergoing emergency patching", "trigger": "Critical security patch applied without notice"},
      {"scenario_id": "EXT_001_S10", "scenario": "Load balancer in front of source system failed", "trigger": "Load balancer health check failure or misconfiguration"}
    ]
  },
  "EXT_002": {
    "component": "Extractor",
    "error_code": "EXT_002",
    "error_message": "Authentication failure at source",
    "severity": "Critical",
    "description": "Credentials for source system are invalid or expired",
    "recommended_action": "Rotate source system credentials and update pipeline config",
    "error_log_url_template": "https://logs.platform.com/errors/EXT_002/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "EXT_002_S1", "scenario": "Service account password expired", "trigger": "Password policy enforcement without pipeline credential update"},
      {"scenario_id": "EXT_002_S2", "scenario": "API key revoked by source system admin", "trigger": "Routine key rotation or security audit"},
      {"scenario_id": "EXT_002_S3", "scenario": "OAuth token expired and refresh failed", "trigger": "Token refresh service unavailable"},
      {"scenario_id": "EXT_002_S4", "scenario": "Source system account locked after failed attempts", "trigger": "Repeated authentication failures triggering lockout policy"},
      {"scenario_id": "EXT_002_S5", "scenario": "IAM role permissions revoked", "trigger": "IAM policy change by cloud admin"},
      {"scenario_id": "EXT_002_S6", "scenario": "Certificate-based auth cert expired", "trigger": "Client certificate not renewed before expiry"},
      {"scenario_id": "EXT_002_S7", "scenario": "MFA requirement added to source system", "trigger": "New security policy requiring MFA for service accounts"},
      {"scenario_id": "EXT_002_S8", "scenario": "Incorrect credentials stored in secrets manager", "trigger": "Manual error during credential rotation"},
      {"scenario_id": "EXT_002_S9", "scenario": "Source system migrated to new auth provider", "trigger": "Auth provider migration without pipeline reconfiguration"},
      {"scenario_id": "EXT_002_S10", "scenario": "IP allowlist updated excluding pipeline worker IP", "trigger": "Network infrastructure change removing pipeline IP from allowlist"}
    ]
  },
  "EXT_003": {
    "component": "Extractor",
    "error_code": "EXT_003",
    "error_message": "Extraction timeout",
    "severity": "High",
    "description": "Source system did not respond within the configured timeout window",
    "recommended_action": "Increase timeout threshold or investigate source system latency",
    "error_log_url_template": "https://logs.platform.com/errors/EXT_003/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "EXT_003_S1", "scenario": "Source query taking too long due to missing index", "trigger": "Index dropped or not created for large table"},
      {"scenario_id": "EXT_003_S2", "scenario": "Source system under heavy read load from other processes", "trigger": "Concurrent reporting jobs consuming source resources"},
      {"scenario_id": "EXT_003_S3", "scenario": "Network latency spike between pipeline and source", "trigger": "Cross-region data transfer congestion"},
      {"scenario_id": "EXT_003_S4", "scenario": "Source system disk I/O saturation", "trigger": "Disk throughput limit reached on source host"},
      {"scenario_id": "EXT_003_S5", "scenario": "Large data volume exceeding timeout window", "trigger": "Unexpected data growth at source without timeout adjustment"},
      {"scenario_id": "EXT_003_S6", "scenario": "Source system garbage collection pause", "trigger": "JVM garbage collection causing response delay"},
      {"scenario_id": "EXT_003_S7", "scenario": "Connection pool exhausted at source", "trigger": "Too many concurrent connections consuming available pool"},
      {"scenario_id": "EXT_003_S8", "scenario": "Source database deadlock causing query delay", "trigger": "Concurrent write and read transactions deadlocking"},
      {"scenario_id": "EXT_003_S9", "scenario": "Proxy server between pipeline and source timing out", "trigger": "Proxy server misconfiguration or overload"},
      {"scenario_id": "EXT_003_S10", "scenario": "Source system CPU throttling under sustained load", "trigger": "Cloud instance CPU credit exhaustion"}
    ]
  },
  "TRF_001": {
    "component": "Transformer",
    "error_code": "TRF_001",
    "error_message": "Schema mismatch detected",
    "severity": "High",
    "description": "Source data schema does not match the expected target schema",
    "recommended_action": "Review schema changes at source and update transformation rules",
    "error_log_url_template": "https://logs.platform.com/errors/TRF_001/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "TRF_001_S1", "scenario": "New column added at source not present in target schema", "trigger": "Source team added column without notifying pipeline team"},
      {"scenario_id": "TRF_001_S2", "scenario": "Column renamed at source breaking field mapping", "trigger": "Source system refactoring without backward compatibility"},
      {"scenario_id": "TRF_001_S3", "scenario": "Column data type changed at source", "trigger": "Source database schema migration"},
      {"scenario_id": "TRF_001_S4", "scenario": "Column removed from source that target expects", "trigger": "Source deprecation of field without pipeline update"},
      {"scenario_id": "TRF_001_S5", "scenario": "Table structure reorganised at source", "trigger": "Source system normalisation or denormalisation"},
      {"scenario_id": "TRF_001_S6", "scenario": "Nested JSON structure changed at source API", "trigger": "Source API version upgrade changing response structure"},
      {"scenario_id": "TRF_001_S7", "scenario": "Date format changed at source", "trigger": "Source system locale or timezone configuration change"},
      {"scenario_id": "TRF_001_S8", "scenario": "Encoding change at source causing character mismatch", "trigger": "Source system migrated from Latin-1 to UTF-8"},
      {"scenario_id": "TRF_001_S9", "scenario": "Target BigQuery schema updated without transformation rule update", "trigger": "Target schema evolution not reflected in transformation layer"},
      {"scenario_id": "TRF_001_S10", "scenario": "Source sending additional metadata fields not in target schema", "trigger": "Source system instrumentation adding debug fields to payload"}
    ]
  },
  "TRF_002": {
    "component": "Transformer",
    "error_code": "TRF_002",
    "error_message": "Null value in non-nullable field",
    "severity": "High",
    "description": "Source data contains null values in fields that do not allow nulls",
    "recommended_action": "Add null handling logic in transformation layer or fix source data",
    "error_log_url_template": "https://logs.platform.com/errors/TRF_002/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "TRF_002_S1", "scenario": "Mandatory customer ID field null for new record type", "trigger": "New record category introduced at source without ID assignment"},
      {"scenario_id": "TRF_002_S2", "scenario": "Transaction amount null due to incomplete source transaction", "trigger": "Partial transaction records created during source system error"},
      {"scenario_id": "TRF_002_S3", "scenario": "Timestamp field null for backfilled historical records", "trigger": "Historical data migration missing timestamp population"},
      {"scenario_id": "TRF_002_S4", "scenario": "Foreign key field null due to orphaned records at source", "trigger": "Referential integrity not enforced at source system"},
      {"scenario_id": "TRF_002_S5", "scenario": "Status field null for records in transition state", "trigger": "Source system writing record before status is assigned"},
      {"scenario_id": "TRF_002_S6", "scenario": "Currency code null for international transactions", "trigger": "Source system not populating currency for certain transaction types"},
      {"scenario_id": "TRF_002_S7", "scenario": "Product code null for bundle or composite products", "trigger": "Bundle products not assigned individual product codes at source"},
      {"scenario_id": "TRF_002_S8", "scenario": "User ID null for system-generated transactions", "trigger": "Automated transactions not assigned a user context"},
      {"scenario_id": "TRF_002_S9", "scenario": "Region field null for global transactions without region mapping", "trigger": "New geography added at source without region mapping update"},
      {"scenario_id": "TRF_002_S10", "scenario": "Account number null due to source masking policy change", "trigger": "Source data masking applied to previously unmasked field"}
    ]
  },
  "TRF_003": {
    "component": "Transformer",
    "error_code": "TRF_003",
    "error_message": "Type casting failure",
    "severity": "Medium",
    "description": "Data type conversion failed during transformation",
    "recommended_action": "Review data type mappings between source and target systems",
    "error_log_url_template": "https://logs.platform.com/errors/TRF_003/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "TRF_003_S1", "scenario": "String value cannot be cast to integer for numeric field", "trigger": "Source sending free-text in a field expected to be numeric"},
      {"scenario_id": "TRF_003_S2", "scenario": "Date string in unexpected format failing date cast", "trigger": "Source system locale change producing different date format"},
      {"scenario_id": "TRF_003_S3", "scenario": "Boolean field receiving string true/false instead of 0/1", "trigger": "Source system upgrade changing boolean representation"},
      {"scenario_id": "TRF_003_S4", "scenario": "Decimal precision loss during float to integer cast", "trigger": "Target field defined as integer for value that contains decimals"},
      {"scenario_id": "TRF_003_S5", "scenario": "Large integer overflow during type conversion", "trigger": "Source value exceeding target field size limit"},
      {"scenario_id": "TRF_003_S6", "scenario": "Currency amount string containing symbol failing numeric cast", "trigger": "Source sending amount as currency string e.g. $1,234.56"},
      {"scenario_id": "TRF_003_S7", "scenario": "Timestamp with timezone failing UTC cast", "trigger": "Source sending timezone-aware timestamp to UTC-only target field"},
      {"scenario_id": "TRF_003_S8", "scenario": "Enum value not matching target allowed values list", "trigger": "New enum value added at source not added to target schema"},
      {"scenario_id": "TRF_003_S9", "scenario": "Binary data field cast to string causing encoding error", "trigger": "Source sending binary blob in text field"},
      {"scenario_id": "TRF_003_S10", "scenario": "Array field cast to scalar failing for multi-value records", "trigger": "Source sending comma-separated values in single-value field"}
    ]
  },
  "VAL_001": {
    "component": "Validator",
    "error_code": "VAL_001",
    "error_message": "Record count mismatch",
    "severity": "High",
    "description": "Number of records at target does not match source record count",
    "recommended_action": "Investigate data loss during extraction or transformation stage",
    "error_log_url_template": "https://logs.platform.com/errors/VAL_001/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "VAL_001_S1", "scenario": "Records dropped during transformation due to filter logic error", "trigger": "Incorrect filter condition in transformation rule"},
      {"scenario_id": "VAL_001_S2", "scenario": "Partial extraction due to source pagination error", "trigger": "API pagination token expiring mid-extraction"},
      {"scenario_id": "VAL_001_S3", "scenario": "Duplicate records deduplicated unexpectedly during load", "trigger": "Deduplication logic applied to non-duplicate records"},
      {"scenario_id": "VAL_001_S4", "scenario": "Records lost during network transmission", "trigger": "Network packet loss during large data transfer"},
      {"scenario_id": "VAL_001_S5", "scenario": "Source record count changed between extraction start and validation", "trigger": "Source system writing new records during extraction window"},
      {"scenario_id": "VAL_001_S6", "scenario": "Null records filtered out that should have been loaded", "trigger": "Overly aggressive null filtering in transformation"},
      {"scenario_id": "VAL_001_S7", "scenario": "Batch split causing partial load to target", "trigger": "Batch processing error dropping one or more sub-batches"},
      {"scenario_id": "VAL_001_S8", "scenario": "Target write rollback due to partial failure", "trigger": "Transaction rollback on target leaving fewer records than expected"},
      {"scenario_id": "VAL_001_S9", "scenario": "Records rejected by target schema validation", "trigger": "Target enforcing stricter validation than transformation layer"},
      {"scenario_id": "VAL_001_S10", "scenario": "Incremental load missing records from boundary window", "trigger": "Watermark logic error in incremental extraction query"}
    ]
  },
  "VAL_002": {
    "component": "Validator",
    "error_code": "VAL_002",
    "error_message": "Duplicate records detected",
    "severity": "Medium",
    "description": "Target dataset contains duplicate records after ingestion",
    "recommended_action": "Add deduplication logic in transformation or loader stage",
    "error_log_url_template": "https://logs.platform.com/errors/VAL_002/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "VAL_002_S1", "scenario": "Pipeline re-run after failure loading same data twice", "trigger": "Manual re-trigger without clearing previously loaded records"},
      {"scenario_id": "VAL_002_S2", "scenario": "Overlapping extraction windows loading same records", "trigger": "Watermark boundary overlap in incremental load config"},
      {"scenario_id": "VAL_002_S3", "scenario": "Source system sending same event twice due to retry logic", "trigger": "Source retry mechanism producing duplicate events"},
      {"scenario_id": "VAL_002_S4", "scenario": "Merge logic failing and inserting instead of updating", "trigger": "MERGE statement condition not matching existing records"},
      {"scenario_id": "VAL_002_S5", "scenario": "Multiple pipeline instances running simultaneously", "trigger": "Parallel job execution triggered by orchestrator misconfiguration"},
      {"scenario_id": "VAL_002_S6", "scenario": "CDC change events replayed from beginning", "trigger": "Change data capture offset reset to earliest position"},
      {"scenario_id": "VAL_002_S7", "scenario": "Target partition overwrite loading data twice", "trigger": "Partition overwrite mode applied to wrong date partition"},
      {"scenario_id": "VAL_002_S8", "scenario": "Lookup table join producing fan-out duplicates", "trigger": "One-to-many join in transformation producing multiple rows per source record"},
      {"scenario_id": "VAL_002_S9", "scenario": "Backfill job overlapping with regular incremental load", "trigger": "Backfill date range overlapping with live incremental window"},
      {"scenario_id": "VAL_002_S10", "scenario": "Source snapshot including previously deleted and re-inserted records", "trigger": "Source soft-delete pattern causing records to reappear in snapshot"}
    ]
  },
  "VAL_003": {
    "component": "Validator",
    "error_code": "VAL_003",
    "error_message": "Missing mandatory fields",
    "severity": "Critical",
    "description": "One or more mandatory fields are absent in the source payload",
    "recommended_action": "Validate source payload structure before ingestion starts",
    "error_log_url_template": "https://logs.platform.com/errors/VAL_003/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "VAL_003_S1", "scenario": "Source API response missing required fields for new record type", "trigger": "New record category introduced at source without full field population"},
      {"scenario_id": "VAL_003_S2", "scenario": "Mandatory primary key field absent from source extract", "trigger": "Source query not selecting all required fields"},
      {"scenario_id": "VAL_003_S3", "scenario": "Required audit fields missing from source system", "trigger": "Source system audit logging disabled or misconfigured"},
      {"scenario_id": "VAL_003_S4", "scenario": "Mandatory date field absent for records created via bulk import", "trigger": "Bulk import tool not populating all required fields"},
      {"scenario_id": "VAL_003_S5", "scenario": "Required reference data field missing after source refactoring", "trigger": "Source system removed field assumed mandatory by pipeline"},
      {"scenario_id": "VAL_003_S6", "scenario": "Mandatory customer segment field missing for B2B transactions", "trigger": "B2B transaction type not mapped to customer segment logic"},
      {"scenario_id": "VAL_003_S7", "scenario": "Required geo fields absent for mobile transactions", "trigger": "Mobile app not sending location data when permissions denied"},
      {"scenario_id": "VAL_003_S8", "scenario": "Compliance-required fields absent from source payload", "trigger": "Source system compliance module disabled during maintenance"},
      {"scenario_id": "VAL_003_S9", "scenario": "Mandatory fields present in schema but not populated by source ORM", "trigger": "ORM layer not mapping all fields during source code update"},
      {"scenario_id": "VAL_003_S10", "scenario": "Required fields missing for records migrated from legacy system", "trigger": "Legacy system not storing fields that new system requires"}
    ]
  },
  "LOD_001": {
    "component": "Loader",
    "error_code": "LOD_001",
    "error_message": "Write timeout to target",
    "severity": "High",
    "description": "Target system did not acknowledge write within timeout window",
    "recommended_action": "Check target system load and increase write timeout threshold",
    "error_log_url_template": "https://logs.platform.com/errors/LOD_001/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "LOD_001_S1", "scenario": "BigQuery slot exhaustion causing write queue backup", "trigger": "Concurrent heavy analytical queries consuming all available slots"},
      {"scenario_id": "LOD_001_S2", "scenario": "Target table locked by concurrent DML operation", "trigger": "Another process running UPDATE or DELETE on target table"},
      {"scenario_id": "LOD_001_S3", "scenario": "Large batch size exceeding write timeout threshold", "trigger": "Data volume spike without corresponding timeout adjustment"},
      {"scenario_id": "LOD_001_S4", "scenario": "Target dataset in different region causing latency", "trigger": "Cross-region write with insufficient timeout configuration"},
      {"scenario_id": "LOD_001_S5", "scenario": "Network bottleneck between loader and BigQuery", "trigger": "Network saturation during peak ingestion window"},
      {"scenario_id": "LOD_001_S6", "scenario": "Target table schema validation causing write delay", "trigger": "Schema validation overhead for wide tables with many columns"},
      {"scenario_id": "LOD_001_S7", "scenario": "Streaming insert buffer full at BigQuery", "trigger": "High-frequency streaming inserts exceeding buffer capacity"},
      {"scenario_id": "LOD_001_S8", "scenario": "GCS staging bucket write slow due to bucket policy scan", "trigger": "Data Loss Prevention scan applied to staging bucket"},
      {"scenario_id": "LOD_001_S9", "scenario": "Target write timeout due to VPC service control policy check", "trigger": "VPC-SC policy evaluation adding latency to every write request"},
      {"scenario_id": "LOD_001_S10", "scenario": "Loader worker running out of memory during write operation", "trigger": "In-memory buffer size insufficient for large payload"}
    ]
  },
  "LOD_002": {
    "component": "Loader",
    "error_code": "LOD_002",
    "error_message": "Partition error at target",
    "severity": "High",
    "description": "Target table partition could not be created or written to",
    "recommended_action": "Review partition configuration and target table schema",
    "error_log_url_template": "https://logs.platform.com/errors/LOD_002/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "LOD_002_S1", "scenario": "Partition expiry date reached and partition auto-deleted", "trigger": "Partition TTL policy expiring active partitions"},
      {"scenario_id": "LOD_002_S2", "scenario": "Writing to future date partition not yet created", "trigger": "Timestamp in source data ahead of current date"},
      {"scenario_id": "LOD_002_S3", "scenario": "Partition column value null causing routing failure", "trigger": "NULL partition decorator not enabled on target table"},
      {"scenario_id": "LOD_002_S4", "scenario": "Partition limit of 4000 per table reached", "trigger": "Daily partitioned table accumulating beyond BigQuery limit"},
      {"scenario_id": "LOD_002_S5", "scenario": "Partition filter required but not provided in write query", "trigger": "Table requires partition filter and loader not providing one"},
      {"scenario_id": "LOD_002_S6", "scenario": "Ingestion time partitioning conflict with field partitioning", "trigger": "Table migrated from ingestion-time to field partitioning without loader update"},
      {"scenario_id": "LOD_002_S7", "scenario": "Partition decorator format incorrect in load job", "trigger": "Date format mismatch in partition decorator parameter"},
      {"scenario_id": "LOD_002_S8", "scenario": "Target partition in read-only state due to active query", "trigger": "Long-running query locking partition during write attempt"},
      {"scenario_id": "LOD_002_S9", "scenario": "Clustering key change invalidating existing partition structure", "trigger": "Target table clustering columns changed without partition rebuild"},
      {"scenario_id": "LOD_002_S10", "scenario": "Cross-partition write violating single partition write policy", "trigger": "Loader attempting to write to multiple partitions in single job"}
    ]
  },
  "LOD_003": {
    "component": "Loader",
    "error_code": "LOD_003",
    "error_message": "Target quota exceeded",
    "severity": "Critical",
    "description": "BigQuery write quota exceeded for the current billing period",
    "recommended_action": "Review quota limits and request quota increase from GCP console",
    "error_log_url_template": "https://logs.platform.com/errors/LOD_003/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "LOD_003_S1", "scenario": "Daily table insert quota exceeded across all pipelines", "trigger": "Too many concurrent pipelines writing to same project"},
      {"scenario_id": "LOD_003_S2", "scenario": "Streaming insert rows per second quota hit", "trigger": "High-frequency streaming pipeline exceeding per-second limit"},
      {"scenario_id": "LOD_003_S3", "scenario": "Load job bytes per day quota exceeded", "trigger": "Large backfill job consuming entire daily byte quota"},
      {"scenario_id": "LOD_003_S4", "scenario": "API requests per minute quota exceeded", "trigger": "Too many small load jobs hitting API rate limit"},
      {"scenario_id": "LOD_003_S5", "scenario": "Concurrent load jobs per table quota exceeded", "trigger": "Multiple pipelines writing to same table simultaneously"},
      {"scenario_id": "LOD_003_S6", "scenario": "Project-level BigQuery quota exhausted by another team", "trigger": "Shared project quota consumed by data science batch jobs"},
      {"scenario_id": "LOD_003_S7", "scenario": "Streaming inserts per table per second quota hit", "trigger": "Single high-volume pipeline exceeding per-table streaming limit"},
      {"scenario_id": "LOD_003_S8", "scenario": "Dataset-level quota set by admin lower than pipeline needs", "trigger": "Dataset quota restricted without pipeline team notification"},
      {"scenario_id": "LOD_003_S9", "scenario": "Quota reset delayed causing gap in available quota", "trigger": "GCP quota reset timing mismatch with pipeline schedule"},
      {"scenario_id": "LOD_003_S10", "scenario": "Emergency quota reduction applied by GCP during service stress", "trigger": "GCP platform-wide quota adjustment during high-demand period"}
    ]
  },
  "ORC_001": {
    "component": "Orchestrator",
    "error_code": "ORC_001",
    "error_message": "DAG execution failure",
    "severity": "Critical",
    "description": "The directed acyclic graph for this pipeline failed to execute",
    "recommended_action": "Review DAG logs in Airflow and check for upstream task failures",
    "error_log_url_template": "https://logs.platform.com/errors/ORC_001/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "ORC_001_S1", "scenario": "DAG import error due to Python syntax error in DAG file", "trigger": "Code deployment introducing syntax error in DAG definition"},
      {"scenario_id": "ORC_001_S2", "scenario": "Airflow scheduler process crashed during DAG execution", "trigger": "Scheduler resource exhaustion or unhandled exception"},
      {"scenario_id": "ORC_001_S3", "scenario": "DAG run timeout exceeded maximum allowed runtime", "trigger": "Data volume growth causing DAG to exceed dagrun_timeout"},
      {"scenario_id": "ORC_001_S4", "scenario": "Circular dependency introduced in DAG task graph", "trigger": "New task added creating undetected circular dependency"},
      {"scenario_id": "ORC_001_S5", "scenario": "DAG paused by admin during execution", "trigger": "Manual intervention pausing active DAG run"},
      {"scenario_id": "ORC_001_S6", "scenario": "Worker pod evicted during task execution in Kubernetes", "trigger": "Node resource pressure causing pod eviction"},
      {"scenario_id": "ORC_001_S7", "scenario": "DAG variable or connection missing in Airflow metadata", "trigger": "Environment variable or connection not migrated to new Airflow instance"},
      {"scenario_id": "ORC_001_S8", "scenario": "Zombie task left from previous failed run blocking new run", "trigger": "Previous DAG run not cleaned up properly leaving zombie tasks"},
      {"scenario_id": "ORC_001_S9", "scenario": "Airflow database connection pool exhausted", "trigger": "Too many concurrent DAG runs overwhelming metadata database"},
      {"scenario_id": "ORC_001_S10", "scenario": "DAG file deleted or moved causing scheduler to lose DAG definition", "trigger": "Accidental deletion or repository restructuring removing DAG file"}
    ]
  },
  "ORC_002": {
    "component": "Orchestrator",
    "error_code": "ORC_002",
    "error_message": "Upstream dependency not met",
    "severity": "High",
    "description": "A required upstream pipeline or dataset was not available",
    "recommended_action": "Check upstream pipeline status and resolve dependency failures first",
    "error_log_url_template": "https://logs.platform.com/errors/ORC_002/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "ORC_002_S1", "scenario": "Upstream pipeline delayed beyond dependency wait timeout", "trigger": "Upstream data source delayed causing downstream SLA breach"},
      {"scenario_id": "ORC_002_S2", "scenario": "Required upstream dataset not yet available in target location", "trigger": "Upstream job failed silently without triggering downstream block"},
      {"scenario_id": "ORC_002_S3", "scenario": "Cross-DAG dependency sensor timed out waiting for signal", "trigger": "ExternalTaskSensor wait timeout exceeded"},
      {"scenario_id": "ORC_002_S4", "scenario": "Required reference table not refreshed before pipeline start", "trigger": "Reference data refresh job missed its schedule"},
      {"scenario_id": "ORC_002_S5", "scenario": "Upstream API not returning data for expected time window", "trigger": "Upstream system data availability SLA breached"},
      {"scenario_id": "ORC_002_S6", "scenario": "GCS file sensor waiting for file that was not dropped", "trigger": "File-based trigger not receiving expected file from upstream"},
      {"scenario_id": "ORC_002_S7", "scenario": "Database view dependency not refreshed before pipeline query", "trigger": "Materialised view refresh job failed silently"},
      {"scenario_id": "ORC_002_S8", "scenario": "Upstream pipeline producing empty output flagged as failure", "trigger": "Empty output from upstream treated as dependency failure"},
      {"scenario_id": "ORC_002_S9", "scenario": "Cross-environment dependency referencing wrong environment", "trigger": "Pipeline config pointing to prod dependency from dev environment"},
      {"scenario_id": "ORC_002_S10", "scenario": "Upstream SLA window changed without downstream notification", "trigger": "Upstream team changed delivery SLA without updating dependency config"}
    ]
  },
  "ORC_003": {
    "component": "Orchestrator",
    "error_code": "ORC_003",
    "error_message": "Job execution timeout",
    "severity": "High",
    "description": "Pipeline job exceeded maximum allowed execution time",
    "recommended_action": "Optimise pipeline performance or increase job timeout threshold",
    "error_log_url_template": "https://logs.platform.com/errors/ORC_003/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "ORC_003_S1", "scenario": "Data volume spike causing job to run beyond timeout", "trigger": "Month-end or quarter-end data surge without timeout adjustment"},
      {"scenario_id": "ORC_003_S2", "scenario": "Slow transformation logic on unexpectedly large dataset", "trigger": "Source data growth outpacing transformation performance"},
      {"scenario_id": "ORC_003_S3", "scenario": "Worker resource contention causing job slowdown", "trigger": "Shared worker pool under heavy concurrent load"},
      {"scenario_id": "ORC_003_S4", "scenario": "External API call within pipeline hanging indefinitely", "trigger": "Third-party API not returning response without timeout"},
      {"scenario_id": "ORC_003_S5", "scenario": "Database lock wait causing job to stall", "trigger": "Long-running transaction on target holding lock"},
      {"scenario_id": "ORC_003_S6", "scenario": "Retry loop running too many times extending total job time", "trigger": "Retry policy too aggressive on frequently failing step"},
      {"scenario_id": "ORC_003_S7", "scenario": "Memory swap causing severe slowdown on worker", "trigger": "Worker memory exceeded physical RAM causing swap usage"},
      {"scenario_id": "ORC_003_S8", "scenario": "File decompression taking longer than expected", "trigger": "Compressed source file larger than anticipated"},
      {"scenario_id": "ORC_003_S9", "scenario": "Job timeout too short after infrastructure migration", "trigger": "New infrastructure with different performance profile not accounted for"},
      {"scenario_id": "ORC_003_S10", "scenario": "Deadlock between two jobs sharing same resource", "trigger": "Two concurrent jobs waiting on each other to release shared resource"}
    ]
  },
  "PLT_001": {
    "component": "Platform",
    "error_code": "PLT_001",
    "error_message": "GCP service outage",
    "severity": "Critical",
    "description": "Google Cloud Platform service disruption affected pipeline execution",
    "recommended_action": "Monitor GCP status page and retry once service is restored",
    "error_log_url_template": "https://logs.platform.com/errors/PLT_001/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "PLT_001_S1", "scenario": "BigQuery service disruption in pipeline region", "trigger": "GCP regional outage affecting BigQuery availability"},
      {"scenario_id": "PLT_001_S2", "scenario": "Cloud Composer Airflow environment unavailable", "trigger": "GCP Composer service degradation"},
      {"scenario_id": "PLT_001_S3", "scenario": "GCS bucket API returning 503 errors", "trigger": "GCS service disruption in staging bucket region"},
      {"scenario_id": "PLT_001_S4", "scenario": "Dataflow job runner unavailable", "trigger": "GCP Dataflow service outage"},
      {"scenario_id": "PLT_001_S5", "scenario": "Cloud Run worker instances failing to start", "trigger": "GCP Cloud Run service disruption"},
      {"scenario_id": "PLT_001_S6", "scenario": "Secret Manager API unavailable blocking credential retrieval", "trigger": "GCP Secret Manager service degradation"},
      {"scenario_id": "PLT_001_S7", "scenario": "Pub/Sub topic unavailable blocking event-driven pipeline", "trigger": "GCP Pub/Sub service disruption"},
      {"scenario_id": "PLT_001_S8", "scenario": "GCP IAM API unavailable blocking service account auth", "trigger": "GCP IAM service degradation affecting all authenticated calls"},
      {"scenario_id": "PLT_001_S9", "scenario": "Multi-region GCP outage affecting failover target", "trigger": "Simultaneous primary and failover region degradation"},
      {"scenario_id": "PLT_001_S10", "scenario": "GCP maintenance window causing unexpected service restart", "trigger": "Unannounced or early maintenance window impacting running jobs"}
    ]
  },
  "PLT_002": {
    "component": "Platform",
    "error_code": "PLT_002",
    "error_message": "Network connectivity failure",
    "severity": "Critical",
    "description": "Network connection between pipeline components was lost",
    "recommended_action": "Check VPC configuration and network routing rules",
    "error_log_url_template": "https://logs.platform.com/errors/PLT_002/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "PLT_002_S1", "scenario": "VPC peering connection dropped between pipeline and target", "trigger": "VPC peering configuration change or route deletion"},
      {"scenario_id": "PLT_002_S2", "scenario": "Firewall rule update blocking pipeline traffic", "trigger": "Security team updating firewall rules without pipeline team notification"},
      {"scenario_id": "PLT_002_S3", "scenario": "Private Service Connect endpoint misconfigured", "trigger": "PSC endpoint update breaking connectivity to GCP services"},
      {"scenario_id": "PLT_002_S4", "scenario": "Cloud Interconnect link failure", "trigger": "Physical interconnect link degradation or failure"},
      {"scenario_id": "PLT_002_S5", "scenario": "DNS resolution failure within VPC", "trigger": "Internal DNS server unavailable or misconfigured"},
      {"scenario_id": "PLT_002_S6", "scenario": "NAT gateway exhausting available ports", "trigger": "High connection volume exhausting NAT port allocation"},
      {"scenario_id": "PLT_002_S7", "scenario": "Subnet IP range exhausted blocking new connections", "trigger": "All IPs in subnet allocated with no new connections possible"},
      {"scenario_id": "PLT_002_S8", "scenario": "Load balancer health check failing causing traffic drop", "trigger": "Backend service health check failing due to misconfiguration"},
      {"scenario_id": "PLT_002_S9", "scenario": "MTU mismatch causing packet fragmentation and drop", "trigger": "Network infrastructure change causing MTU inconsistency"},
      {"scenario_id": "PLT_002_S10", "scenario": "Cross-cloud connectivity failure for hybrid pipeline", "trigger": "Azure-GCP connectivity disruption for hybrid ingestion pipeline"}
    ]
  },
  "PLT_003": {
    "component": "Platform",
    "error_code": "PLT_003",
    "error_message": "Memory overflow on worker node",
    "severity": "High",
    "description": "Pipeline worker ran out of memory during job execution",
    "recommended_action": "Increase worker memory allocation or optimise data batch size",
    "error_log_url_template": "https://logs.platform.com/errors/PLT_003/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "PLT_003_S1", "scenario": "Worker OOM killed during large dataset transformation", "trigger": "Data volume exceeding worker memory allocation"},
      {"scenario_id": "PLT_003_S2", "scenario": "Memory leak in transformation code accumulating over time", "trigger": "Unbounded list or dictionary growing with each record processed"},
      {"scenario_id": "PLT_003_S3", "scenario": "Multiple jobs scheduled on same worker exhausting shared memory", "trigger": "Worker oversubscribed with concurrent job allocations"},
      {"scenario_id": "PLT_003_S4", "scenario": "In-memory cache not evicting old entries", "trigger": "Cache eviction policy misconfigured allowing unbounded growth"},
      {"scenario_id": "PLT_003_S5", "scenario": "Large JSON payload fully loaded into memory before processing", "trigger": "Non-streaming JSON parsing on large payload"},
      {"scenario_id": "PLT_003_S6", "scenario": "Pandas dataframe holding full dataset in memory", "trigger": "Batch size not configured causing full dataset load into dataframe"},
      {"scenario_id": "PLT_003_S7", "scenario": "Worker node memory reduced during infrastructure right-sizing", "trigger": "Cost optimisation reducing worker memory below job requirements"},
      {"scenario_id": "PLT_003_S8", "scenario": "Third-party library memory leak in pipeline dependency", "trigger": "Known memory leak in pinned library version"},
      {"scenario_id": "PLT_003_S9", "scenario": "Temporary files accumulating in worker memory filesystem", "trigger": "Temp file cleanup not running between pipeline stages"},
      {"scenario_id": "PLT_003_S10", "scenario": "JVM heap exhaustion on Java-based pipeline worker", "trigger": "JVM heap size not configured for current data volume"}
    ]
  },
  "ADH_001": {
    "component": "Adhoc",
    "error_code": "ADH_001",
    "error_message": "Manual intervention required",
    "severity": "Medium",
    "description": "Job was flagged for manual review and could not proceed automatically",
    "recommended_action": "Review flagged job details and process manually via ops console",
    "error_log_url_template": "https://logs.platform.com/errors/ADH_001/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "ADH_001_S1", "scenario": "Data quality threshold breached requiring human review", "trigger": "Automated quality check flagging anomalous data patterns"},
      {"scenario_id": "ADH_001_S2", "scenario": "Compliance hold placed on data pending legal review", "trigger": "Legal team requesting data hold for regulatory investigation"},
      {"scenario_id": "ADH_001_S3", "scenario": "Sensitive data detected requiring privacy review before load", "trigger": "PII detection scan flagging unexpected sensitive fields"},
      {"scenario_id": "ADH_001_S4", "scenario": "Business rule exception requiring manual approval", "trigger": "Transaction value exceeding automated approval threshold"},
      {"scenario_id": "ADH_001_S5", "scenario": "Conflict between source and previously loaded data requiring reconciliation", "trigger": "Incoming data contradicting existing target records"},
      {"scenario_id": "ADH_001_S6", "scenario": "New data source requiring manual onboarding validation", "trigger": "First-time data source not yet approved for automated ingestion"},
      {"scenario_id": "ADH_001_S7", "scenario": "Regulatory reporting window requiring manual sign-off", "trigger": "End-of-period data requiring compliance officer approval"},
      {"scenario_id": "ADH_001_S8", "scenario": "Data access request requiring manual authorisation", "trigger": "Sensitive dataset access not pre-authorised for pipeline service account"},
      {"scenario_id": "ADH_001_S9", "scenario": "Unusual data volume spike flagged for manual investigation", "trigger": "Volume anomaly detection triggering human review workflow"},
      {"scenario_id": "ADH_001_S10", "scenario": "Cross-border data transfer requiring manual compliance check", "trigger": "Data localisation policy requiring manual review for cross-region transfer"}
    ]
  },
  "ADH_002": {
    "component": "Adhoc",
    "error_code": "ADH_002",
    "error_message": "Configuration change caused failure",
    "severity": "High",
    "description": "A recent configuration change broke the pipeline execution",
    "recommended_action": "Roll back recent configuration changes and retest pipeline",
    "error_log_url_template": "https://logs.platform.com/errors/ADH_002/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "ADH_002_S1", "scenario": "Environment variable changed causing pipeline misconfiguration", "trigger": "DevOps team updating env vars without pipeline team awareness"},
      {"scenario_id": "ADH_002_S2", "scenario": "Pipeline config file updated with incorrect values", "trigger": "Manual config edit introducing incorrect parameter value"},
      {"scenario_id": "ADH_002_S3", "scenario": "Dependency version upgrade breaking pipeline compatibility", "trigger": "Library upgrade introducing breaking API changes"},
      {"scenario_id": "ADH_002_S4", "scenario": "Feature flag change altering pipeline behaviour", "trigger": "Feature flag toggled without assessing pipeline impact"},
      {"scenario_id": "ADH_002_S5", "scenario": "Connection string updated pointing to wrong environment", "trigger": "Config pointing to dev database instead of prod after copy-paste error"},
      {"scenario_id": "ADH_002_S6", "scenario": "Timeout configuration reduced causing previously passing jobs to fail", "trigger": "Performance optimisation reducing timeouts below actual job duration"},
      {"scenario_id": "ADH_002_S7", "scenario": "Batch size configuration changed causing memory overflow", "trigger": "Batch size increased beyond worker memory capacity"},
      {"scenario_id": "ADH_002_S8", "scenario": "Schedule cron expression changed causing missed or duplicate runs", "trigger": "Incorrect cron expression update causing schedule misalignment"},
      {"scenario_id": "ADH_002_S9", "scenario": "Logging configuration change causing pipeline crash", "trigger": "Log sink reconfiguration causing unhandled exception in pipeline"},
      {"scenario_id": "ADH_002_S10", "scenario": "Infrastructure-as-code change modifying pipeline runtime environment", "trigger": "Terraform apply changing worker spec without pipeline team review"}
    ]
  },
  "ADH_003": {
    "component": "Adhoc",
    "error_code": "ADH_003",
    "error_message": "Unknown error",
    "severity": "Medium",
    "description": "An unexpected error occurred that does not match any known error pattern",
    "recommended_action": "Collect full error logs and escalate to platform engineering team",
    "error_log_url_template": "https://logs.platform.com/errors/ADH_003/{job_id}",
    "failure_scenarios": [
      {"scenario_id": "ADH_003_S1", "scenario": "Unhandled exception in pipeline code with no error mapping", "trigger": "Edge case in data triggering code path with no exception handler"},
      {"scenario_id": "ADH_003_S2", "scenario": "Third-party service returning unexpected response format", "trigger": "External dependency changing response format without notice"},
      {"scenario_id": "ADH_003_S3", "scenario": "Race condition between concurrent pipeline components", "trigger": "Timing-dependent bug triggered under specific load conditions"},
      {"scenario_id": "ADH_003_S4", "scenario": "Cosmic ray bit flip causing memory corruption", "trigger": "Hardware-level random bit error in worker memory"},
      {"scenario_id": "ADH_003_S5", "scenario": "Pipeline failing due to clock skew between components", "trigger": "NTP sync failure causing timestamp comparison errors"},
      {"scenario_id": "ADH_003_S6", "scenario": "Encoding error from unexpected unicode character in source data", "trigger": "Rare unicode character in source data not handled by pipeline"},
      {"scenario_id": "ADH_003_S7", "scenario": "Intermittent failure with no reproducible pattern", "trigger": "Non-deterministic failure with no consistent root cause identified"},
      {"scenario_id": "ADH_003_S8", "scenario": "Pipeline failure due to leap second or daylight saving time transition", "trigger": "Time boundary edge case causing timestamp arithmetic error"},
      {"scenario_id": "ADH_003_S9", "scenario": "Failure caused by interaction between two independently working components", "trigger": "Emergent failure from component interaction not caught in unit testing"},
      {"scenario_id": "ADH_003_S10", "scenario": "Silent data corruption causing downstream validation failure", "trigger": "Data corrupted without error at source causing failure at validation stage"}
    ]
  }
}

# Write to file
output_path = os.path.join(os.path.dirname(__file__), "data", "error_codes.json")
with open(output_path, "w") as f:
    json.dump(error_codes, f, indent=2)

print(f"✅ error_codes.json written successfully to {output_path}")
print(f"✅ Total error codes: {len(error_codes)}")
total_scenarios = sum(len(v['failure_scenarios']) for v in error_codes.values())
print(f"✅ Total failure scenarios: {total_scenarios}")
