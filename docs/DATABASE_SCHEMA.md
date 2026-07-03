# 🗄️ Database Schema Specification

This document details the relational schemas, indexes, and foreign keys configured in the SQLite database.

---

## 📊 Entity Relationship Table List

### 1. `users`
- Stores system access details for administrators and officers.
  - `id` (INTEGER, Primary Key, Indexed)
  - `username` (VARCHAR, Unique, Indexed)
  - `email` (VARCHAR, Unique, Indexed)
  - `full_name` (VARCHAR)
  - `password_hash` (VARCHAR)
  - `role` (VARCHAR, Default: `"officer"`)
  - `status` (VARCHAR, Default: `"active"`)
  - `created_at` (DATETIME)

### 2. `locations`
- Mapped GIS coordinates for checkpoints.
  - `id` (INTEGER, Primary Key, Indexed)
  - `name` (VARCHAR, Unique, Indexed)
  - `risk_level` (VARCHAR)
  - `lat` (FLOAT), `lng` (FLOAT)

### 3. `cameras`
- CCTV hardware node configurations.
  - `id` (VARCHAR, Primary Key, Indexed) — e.g. `CAM-001`
  - `name` (VARCHAR), `location` (VARCHAR)
  - `location_id` (INTEGER, Foreign Key -> `locations.id`)
  - `ip_address` (VARCHAR)
  - `status` (VARCHAR), `health_status` (VARCHAR)
  - `lat` (FLOAT), `lng` (FLOAT)

### 4. `vehicles`
- Traffic vehicles detected by AI models.
  - `id` (INTEGER, Primary Key, Indexed)
  - `license_plate` (VARCHAR, Unique, Indexed)
  - `type` (VARCHAR), `brand` (VARCHAR), `color` (VARCHAR)
  - `owner_name` (VARCHAR)
  - `status` (VARCHAR) — `valid`, `expired`, `stolen`, `suspended`

### 5. `violations`
- Automatically detected traffic infractions.
  - `id` (INTEGER, Primary Key, Indexed)
  - `vehicle_id` (INTEGER, Foreign Key -> `vehicles.id`)
  - `camera_id` (VARCHAR, Foreign Key -> `cameras.id`)
  - `type` (VARCHAR) — `red_light_jump`, `overspeeding`, `no_helmet`, etc.
  - `timestamp` (DATETIME, Indexed)
  - `fine_amount` (FLOAT), `status` (VARCHAR, Indexed) — `pending`, `paid`, `resolved`
  - `evidence_image_path` (VARCHAR), `evidence_video_path` (VARCHAR)
  - `confidence_score` (FLOAT)
  - `created_at` (DATETIME, Indexed)

### 6. `fine_rules`
- Fine tariffs lookup table.
  - `id` (INTEGER, Primary Key, Indexed)
  - `violation_type` (VARCHAR, Unique, Indexed)
  - `amount` (FLOAT), `description` (VARCHAR)

### 7. `payments`
- Challan transaction history logs.
  - `id` (INTEGER, Primary Key, Indexed)
  - `violation_id` (INTEGER, Foreign Key -> `violations.id`)
  - `amount` (FLOAT)
  - `transaction_id` (VARCHAR, Unique, Indexed)
  - `payment_method` (VARCHAR), `status` (VARCHAR)

### 8. `notifications`
- Core real-time alert logs.
  - `id` (INTEGER, Primary Key, Indexed)
  - `user_id` (INTEGER, Foreign Key -> `users.id`, Nullable)
  - `title` (VARCHAR), `message` (TEXT), `type` (VARCHAR)
  - `is_read` (BOOLEAN, Default: `False`, Indexed)
  - `created_at` (DATETIME, Default: `now`, Indexed)
