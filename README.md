
# 🧠 Distributed Log Normalization & Traceability POC

This proof of concept (POC) demonstrates how to ingest logs from distributed systems — even when they follow inconsistent formats — and normalize them into a unified schema for observability, traceability, and historical analysis.

---

## ✅ Overview

This system:

- Ingests logs via **Kafka** from multiple distributed systems (structured and unstructured)
- Normalizes log events to a consistent schema
- Joins multi-part logs (e.g., events and error details)
- Stores results in **SQLite** for querying and analysis
- Provides test coverage for key modules
- Includes Kafka UI (optional) for inspecting topic messages

---

## 🏗 Architecture

```
+-------------------+      +------------------+      +------------------+      +-------------------+
|   fedebom         |      |      cmf         |      |      bcis        |      |    reporting      |
+-------------------+      +------------------+      +------------------+      +-------------------+
        |                          |                        |                          |
        +-----------+--------------+------------------------+--------------------------+
                                    |
                                    v
                         +----------------------+
                         |   Kafka Topic:       |
                         |      raw-logs        |
                         +----------------------+
                                    |
                                    v
                         +----------------------+
                         |   Kafka Consumer     |
                         |   (Normalizer)       |
                         +----------------------+
                                    |
                                    v
                         +----------------------+
                         |   SQLite Database    |
                         |   event_history.db   |
                         +----------------------+
                                    |
                                    v
                         +----------------------+
                         | Export / Analytics   |
                         +----------------------+
```


---

## 💾 Normalized Schema

| Field           | Description                                |
|----------------|--------------------------------------------|
| `system_id`     | Originating system (e.g. `fedebom`, `bcis`) |
| `checkpoint_id` | Processing stage or label                  |
| `timestamp`     | Event timestamp (ISO format)               |
| `status`        | `SUCCESS` or `FAILURE`                     |
| `correlation_id`| Trace ID for joining related events        |
| `failure_reason`| Optional reason for failure (if any)       |

---

## 🔌 Systems Overview

Each system (producer) represents a different real-world logging style, allowing us to demonstrate normalization of diverse formats.

| System       | Format             | Failure Detail             | Notes                                                                 |
|--------------|--------------------|-----------------------------|-----------------------------------------------------------------------|
| `fedebom`    | Structured JSON     | Separate JSON log           | Emits a checkpoint log, and if failed, emits a second log with error detail |
| `reporting`  | Structured JSON     | Inline in log               | Emits one structured log that includes both the event and error fields |
| `bcis`       | Unstructured text   | Inline in log               | Emits plain-text logs with both status and failure reason included    |
| `cmf`        | Unstructured text   | Separate plain-text log     | Similar to `fedebom` but logs are in plain text instead of JSON       |

---

## 🗂 Supported Systems and Log Examples

### ✅ `fedebom` (structured, multi-log join)
- **Main log:** JSON with `status` and `checkpoint`
- **Failure reason:** separate log with same `correlation_id`

**Checkpoint log:**
```
{
  "system": "fedebom",
  "checkpoint": "CHECKPOINT_1",
  "status": "FAILURE",
  "timestamp": "2025-05-04T10:30:00",
  "correlation_id": "abc-123"
}
```

**Separate error log:**
```
{
  "system": "fedebom",
  "correlation_id": "abc-123",
  "failure_reason": "FAILURE_REASON_2"
}
```
### ✅ `reporting` (structured, inline error)
- Single JSON log with failure reason inline if `status == "FAILURE"`
```
{
  "system": "reporting",
  "checkpoint": "REPORTING_CHECKPOINT_2",
  "status": "FAILURE",
  "timestamp": "2025-05-04T10:33:00",
  "correlation_id": "ghi-789",
  "failure_reason": "REPORTING_FAILURE_REASON_2"
}
```


### ✅ `cmf` (unstructured, multi-log join)
**Checkpoint log:**
```
2025-05-04T10:32:00 CMF: CMF_CHECKPOINT_2 - FAILURE (ID: def-456)
```

**Separate error log:**
```
2025-05-04T10:32:01 CMF CMF_ERROR: (ID: def-456) - CMF_FAILURE_REASON_1
```

### ✅ `bcis` (unstructured, single-log)
**Checkpoint log:**
```
2025-05-04T10:30:00 BCIS: CHECKPOINT_B - FAILURE (ID: abc-123) - FAILURE_REASON_X
```
```
2025-05-04T10:30:00 BCIS: CHECKPOINT_A - SUCCESS (ID: abc-123)
```
---

Example Flow from Orchestrator:
-------------------------------
```
1. Orchestrator starts and triggers a new correlation_id

2. Fedebom system begins:
   → INITIATED (SUCCESS)
   → CHECKPOINT_1 (FAILURE)
     ↳ [Failure reason emitted separately]
   → CHECKPOINT_1 (SUCCESS)
   → CHECKPOINT_2 (SUCCESS)
   → FINALIZED (SUCCESS)

3. Orchestrator randomly chooses the next downstream path:
   a. Fedebom → CMF → Reporting and BCIS in parallel
   b. Fedebom → Reporting and BCIS in parallel

4. If CMF is chosen:
   → CMF: CMF_CHECKPOINT_1 (SUCCESS)
   → CMF: CMF_CHECKPOINT_2 (FAILURE)
     ↳ CMF_ERROR log sent separately with failure reason
   → CMF: CMF_CHECKPOINT_2 (SUCCESS)
   → CMF: CMF_FINALIZED (SUCCESS)

5. Reporting system logs:
   → REPORTING_INITIATED → REPORTING_CHECKPOINT_1 → ... → REPORTING_FINALIZED  


6. BCIS system logs:
   → BCIS_INITIALIZED → BCIS_CHECKPOINT_1 → ... → BCIS_FINALIZED  


7. Each step emits logs to Kafka → parsed → normalized → stored in SQLite
```

---

## 📂 Project Structure

```bash
distributed-tracing/
├── README.md
├── orchestrator.py
├── docker-compose.yml
├── requirements.txt
├── .gitignore
│
├── db/
│   ├── schema_setup.py
│   └── event_history.db
│
├── consumer.py
│
├── flow_engine/
│   ├── __init__.py
│   └── flow_engine.py
│
├── log_parsers/
│   ├── __init__.py
│   ├── structured.py
│   ├── bcis.py
│   └── cmf.py
│
├── producers/
│   ├── producer_fedebom.py
│   ├── producer_cmf.py
│   ├── producer_bcis.py
│   └── producer_reporting.py
│
├── kui/
│   └── config.yml
│
# └── tests/
#     ├── conftest.py
#     ├── test_flow_engine.py
#     └── test_parsers/
#         ├── test_structured.py
#         ├── test_bcis.py
#         └── test_cmf.py
```

---

## 🚀 Getting Started

### 1. Create Virtual Environment & Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start Kafka + Zookeeper + Kafka UI

```bash
docker-compose up -d
```

### 3. Set Up SQLite Schema

```bash
python db/schema_setup.py
```

### 4. Run the Consumer

```bash
python consumer.py
```

### 5. Run the Orchestrator

```bash
python orchestrator.py
```

---

## 🧪 Run Tests

```bash
PYTHONPATH=. pytest tests/
```

---



---

## 🧰 Helpful Commands

### View Kafka Logs Persisted
```bash
sqlite3 db/event_history.db
SELECT * FROM events;
```

### Export to Pandas (in Python)
```python
import pandas as pd
df = pd.read_sql("SELECT * FROM events", sqlite3.connect("db/event_history.db"))
```
