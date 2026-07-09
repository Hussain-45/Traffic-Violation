# Admin Dashboard Subsystem Documentation

This document describes the design, architecture, endpoints, and components of the Admin Dashboard subsystem implemented in Step 22.

---

## 1. Subsystem Architecture

The Admin Dashboard provides real-time system resource gauges, interactive camera feed toggles/restarts, user security configuration (role/status management), dynamic system properties config editing, and backend stdout/stderr log tailing. 

```
                                    +------------------------------+
                                    |       Admin Dashboard        |
                                    |   (React / Next.js Client)   |
                                    +--------------+---------------+
                                                   |
                                                   | HTTP REST Requests
                                                   v
                                    +--------------+---------------+
                                    |     FastAPI Admin Router     |
                                    |    (backend/app/api/v1/)     |
                                    +--------------+---------------+
                                                   |
                                                   v
                                    +--------------+---------------+
                                    |       AdminController        |
                                    | (backend/app/controllers/)   |
                                    +--------------+---------------+
                                                   |
                                                   v
                                    +--------------+---------------+
                                    |         AdminService         |
                                    |   (backend/app/services/)    |
                                    +-------+---------------+------+
                                            |               |
                    +-----------------------v-------+       +------v-----------------------+
                    |        SqlAlchemy ORM         |       |      PSUTIL System API       |
                    | (SQLite Metadata & Activity)  |       | (CPU / Memory / Disk / Log)  |
                    +-------------------------------+       +------------------------------+
```

---

## 2. Backend Architecture

### 2.1 Schema Definition (`backend/app/schemas/admin_schema.py`)
Defines standard response schemas for:
- `DashboardSummaryResponse`: Summary cards (total violations, active user counts, online cameras).
- `SystemStatusResponse`: CPU, memory usage, disk allocations, and uptime.
- `ConfigSettingsResponse` & `ConfigSettingsUpdate`: Dynamic settings editing (SMTP credentials, confidence thresholds, enabled pipeline AI modules).
- `AuditLogResponse`: Administrative chronological audit trace.
- `HealthStatusResponse`: Database connectivity, API status, and system capacity indicators.

### 2.2 Business Logic (`backend/app/services/admin_service.py`)
- Reads and parses local server system log files (`app.log` or default console streams).
- Dynamically parses and updates `config.yaml` or `.env` parameters using standard safe-writers.
- Communicates through SQLite ORM relationships for camera configuration and user metadata updates.
- Inserts audit logs for all security actions into `ActivityLog`.

### 2.3 API Route Registry (`backend/app/api/v1/admin.py` & `router.py`)
Exposes REST endpoints protected by `check_admin_role` dependency authorization:
- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/system`
- `GET /api/v1/admin/cameras`
- `POST /api/v1/admin/cameras/{camera_id}/toggle`
- `POST /api/v1/admin/cameras/{camera_id}/restart`
- `GET /api/v1/admin/users`
- `PUT /api/v1/admin/users/{user_id}`
- `GET /api/v1/admin/settings`
- `PUT /api/v1/admin/settings`
- `GET /api/v1/admin/logs`
- `GET /api/v1/admin/audit`
- `GET /api/v1/admin/health`

---

## 3. Frontend Components

### 3.1 `AdminDashboardPage` (`frontend/src/app/admin/page.tsx`)
Main page controller handling stateful client-side session authentication. Renders authentication panel overlay if JWT token is missing, and provides responsive side nav integration.

### 3.2 `SystemStatusCard` (`frontend/src/components/admin/SystemStatusCard.tsx`)
Displays CPU core percentages, memory limits, and disk space with circular/linear progress bars.

### 3.3 `CameraControlTable` (`frontend/src/components/admin/CameraControlTable.tsx`)
Lists stream channels, current status tags, and provides controls for restarting cameras or toggling feed statuses. Includes an interactive live-preview stream container.

### 3.4 `UserManagementTable` (`frontend/src/components/admin/UserManagementTable.tsx`)
Manages roles (Admin, Officer, Viewer) and access status parameters (Active, Inactive).

### 3.5 `ConfigSettingsForm` (`frontend/src/components/admin/ConfigSettingsForm.tsx`)
Permits dynamic adjustments of confidence thresholds, speed limits, SMTP mail settings, and toggle activations for AI pipeline modules.

### 3.6 `LogViewerConsole` (`frontend/src/components/admin/LogViewerConsole.tsx`)
Monitors tailed logs in a retro-terminal log emulator with automated level-based coloring.
