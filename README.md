# 🧠 Distributed Log Normalization & Traceability POC

This proof of concept (POC) demonstrates how to ingest logs from distributed systems — even when they follow inconsistent formats — and normalize them into a unified schema for observability, traceability, and historical analysis.

---

## ✅ Overview

This system:

- Ingests logs via **Kafka** from multiple distributed systems
- Handles both **structured (JSON)** and **unstructured (plain text)** logs
- Normalizes log events to a consistent schema
- Joins multi-part logs (e.g., events and error details)
- Stores results in **SQLite** for fast querying
- Exports normalized data to **CSV** for reporting or analysis

---

## 🏗 Architecture

```
+---------------------+        +-------------------+        +-------------------+        +-------------+
|  producer_fedebom   | ---->  |                   | ---->  |                   | ---->  |             |
| (structured logs)   |        |    Kafka Topic    |        |  log_consumer.py  |        |  SQLite DB  |
+---------------------+        |     raw-logs      |        +-------------------+        +-------------+
+---------------------+        |                   |
|   producer_bcis     | ---->  |                   |
|  (unstructured)     |        +-------------------+
+---------------------+
```


---

## 💾 Normalized Schema

All logs are normalized into the following format:

| Field           | Description                               |
|----------------|-------------------------------------------|
| `system_id`     | Originating system (e.g. `fedebom`, `bcis`) |
| `checkpoint_id` | Processing stage or status label          |
| `timestamp`     | Event timestamp (ISO format)              |
| `status`        | `SUCCESS` or `FAILURE`                    |
| `correlation_id`| Trace ID for joining related events       |
| `failure_reason`| Optional reason for failure (if any)      |

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

### 🧪 Log Examples

---

### `FEDEBOM`

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

---

### `BCIS`

**Checkpoint log:**
```
2025-05-04T10:30:00 BCIS: CHECKPOINT_B - FAILURE (ID: abc-123) - FAILURE_REASON_X
```
```
2025-05-04T10:30:00 BCIS: CHECKPOINT_A - SUCCESS (ID: abc-123)
```

---

### `CMF`

**Checkpoint log:**
```
2025-05-04T10:32:00 CMF: CMF_CHECKPOINT_2 - FAILURE (ID: def-456)
```

**Separate error log:**
```
2025-05-04T10:32:01 CMF CMF_ERROR: (ID: def-456) - CMF_FAILURE_REASON_1
```

---

### `REPORTING`

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

## 📂 Project Structure

```
distributed-tracing/
│
├── db/
│   └── schema_setup.py         # Creates SQLite DB and schema
│
├── producer_fedebom.py         # Emits structured JSON logs (2-part)
├── producer_bcis.py            # Emits unstructured logs (1-line)
│
├── log_consumer.py             # Normalizes and stores events
├── utils/
│   └── export_to_csv.py        # Optional reporting script
│
├── docker-compose.yml          # Kafka + Zookeeper setup
├── event_history.db            # Generated SQLite database
├── README.md                   # This file
```

---

## 🚀 Getting Started

### 1. Start Kafka + Zookeeper

```bash
docker-compose up -d
```
### 2. Activate your virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# OR
.venv\Scripts\activate     # On Windows
```

Then install dependencies
```bash
pip install kafka-python
```


### 2. Set up SQLite database

```bash
python db/schema_setup.py
```

### 3. Start the producers

In two separate terminals:

```bash
python producer_fedebom.py
```

```bash
python producer_bcis.py
```

### 4. Start the consumer

```bash
python log_consumer.py
```

You’ll see logs being normalized and stored in the database.

---

## 📊 Optional: Export Logs to CSV

```bash
python utils/export_to_csv.py
```

Exports logs from SQLite to `normalized_events.csv`.

---

## 📌 Notes

- `fedebom` emits structured logs — event + optional failure reason
- `bcis` emits unstructured logs — single line with embedded data
- The consumer buffers and joins logs by `correlation_id`
- All data is stored in a normalized, queryable format

---

## 📈 Possible Extensions

- Swap SQLite for BigQuery or another cloud-native DB
- Add log parsers for other systems (e.g. `cmf`, `system_N`)
- Build a web-based dashboard for real-time event flow
- Track processing latency between checkpoints

---

## 🙌 Acknowledgments

- Built as a system design POC and internal demo for distributed observability.
