# Analytics & Reporting Subsystem

This document provides a comprehensive overview of the **Analytics & Reporting** module designed to track vehicle traffic flows, rule violation statistics, AI detection confidence levels, and email notification delivery states.

---

## 1. System Architecture

The subsystem implements a strictly decoupled multi-tiered architecture:

```
          ┌───────────────────────────────────────────┐
          │             Database Tables               │
          │ (violations, vehicles, email_logs, etc.)  │
          └─────────────────────┬─────────────────────┘
                                │
                                ▼
          ┌───────────────────────────────────────────┐
          │           AnalyticsRepository             │
          │      (Raw SQL aggregates, period groups)  │
          └─────────────────────┬─────────────────────┘
                                │
                                ▼
          ┌───────────────────────────────────────────┐
          │            AnalyticsService               │
          │      (Performance stats, export engines)  │
          └─────────────────────┬─────────────────────┘
                                │
                                ▼
          ┌───────────────────────────────────────────┐
          │           AnalyticsController             │
          │      (Filter parsing, parameter maps)     │
          └─────────────────────┬─────────────────────┘
                                │
                                ▼
          ┌───────────────────────────────────────────┐
          │              REST API Router              │
          │       (/dashboard, /export, /health)      │
          └───────────────────────────────────────────┘
```

---

## 2. API Endpoints Reference

All endpoints are prefix-mounted under `/api/v1/analytics`.

### 2.1 Consolidated Dashboard Data
* **Endpoint**: `GET /api/v1/analytics/dashboard`
* **Description**: Returns all aggregated charts, trends, top lists, and KPI cards in a single consolidated response.
* **Query Parameters (Filters)**:
  * `start_date`: ISO timestamp filter (e.g., `2026-07-01T00:00:00`)
  * `end_date`: ISO timestamp filter
  * `plate`: Substring search on vehicle plate number
  * `violation_type`: Specific rule filter (`No Helmet`, `Wrong Side`, etc.)
  * `camera_id`: Camera identifier
  * `status`: Violation state (`pending`, `paid`, `resolved`)

### 2.2 Chronological Trends
* **Endpoint**: `GET /api/v1/analytics/trends`
* **Query Parameters**:
  * `interval`: Time grouping interval (`day`, `week`, `month`)
* **Response**: Lists period dates mapped to count counts and total fine sums.

### 2.3 System Health Diagnostics
* **Endpoint**: `GET /api/v1/analytics/health`
* **Response**:
  ```json
  {
    "db_connection": "good",
    "system_uptime": "99.98%",
    "performance_metrics": {
      "avg_processing_latency_ms": 142.5,
      "avg_ocr_confidence": 0.895,
      "avg_ai_confidence": 0.913,
      "module_health_summary": {
        "yolo_detector": "healthy",
        "ocr_reader": "healthy",
        "evidence_generator": "healthy",
        "database_writer": "healthy"
      }
    }
  }
  ```

---

## 3. Data Export Formats

The export module is accessible at `GET /api/v1/analytics/export` and supports:

1. **CSV (`format=csv`)**: Returns flat tabular records with correct content headers.
2. **Excel (`format=xlsx`)**: Returns a downloadable binary spreadsheet.
3. **JSON (`format=json`)**: Returns raw structured JSON list data.
4. **PDF (`format=pdf`)**: Generates a structured plain text document layout summarizing KPI totals and filtered violation list entries.

---

## 4. DB Snapshots Persistency

Pre-computed snapshot models are defined in `backend/app/models/analytics_model.py`:
- **Table name**: `analytics_reports`
- **Fields**:
  - `report_name` (str): Descriptive label.
  - `report_type` (str): Snapshot type (`daily`, `weekly`, `monthly`, `custom`).
  - `summary_data` (JSON): Aggregated KPIs.
