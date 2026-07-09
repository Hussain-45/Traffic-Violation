# Authentication & RBAC Subsystem Documentation

This document describes the design, database schemas, services, endpoints, and frontend components of the Authentication and Role-Based Access Control (RBAC) subsystem implemented in Step 23.

---

## 1. System Architecture

The subsystem protects both REST API routers and client-side view pages from unauthorized access. It utilizes JWT access/refresh token pairs, manages session status limits, tracks consecutive login failures to trigger account lockouts, and maps roles to granular scopes.

```
                         +-----------------------------+
                         |       Client Browser        |
                         |   (React / Next.js Pages)   |
                         +--------------+--------------+
                                        |
                                        | HTTP REST Requests
                                        v
                         +--------------+--------------+
                         |      FastAPI Router         |
                         |    (backend/app/api/v1/)    |
                         +--------------+--------------+
                                        |
                         +--------------v--------------+
                         |    AuthController Mediator  |
                         +--------------+--------------+
                                        |
                 +----------------------+----------------------+
                 v                                             v
     +-----------+-----------+                     +-----------+-----------+
     |      AuthService      |                     |      RBACService      |
     +-----------+-----------+                     +-----------+-----------+
                 |                                             |
         +-------+-------+                                     v
         v               v                             +-------+-------+
  +------+------+ +------+------+                      |  Role Guards  |
  | PasswordSvc | |   JWTSvc    |                      +---------------+
  +-------------+ +-------------+
```

---

## 2. Database Models

- **`User`** (`users`): Maps login credentials, passwords, active roles, consecutive failed attempts count, and locked expiration dates.
- **`Role`** (`roles`): Defines role groups (e.g. `admin`, `officer`, `viewer`).
- **`Permission`** (`permissions`): Defines granular scopes (e.g. `settings`, `logs`, `users`, `reports`).
- **`SessionModel`** (`sessions`): Stores session identifiers, matching refresh tokens, client IP addresses, user agents, revocation flags, and expiration dates.

---

## 3. Backend Services

### 3.1 `PasswordService` (`password_service.py`)
Wraps `bcrypt` for secure UTF-8 password hashing and checks validation matches.

### 3.2 `JWTService` (`jwt_service.py`)
Signs and verifies access tokens (expiry 30m) and refresh tokens (expiry 7 days).

### 3.3 `RBACService` (`rbac_service.py`)
Validates user permission groups. Exposes FastAPI route dependency guard `require_permission`.

### 3.4 `AuthService` (`auth_service.py`)
Verifies passwords, increases failed attempts count, enforces a 15-minute lockout if attempts exceed 5, and logs audit events in `ActivityLog`.

---

## 4. REST API Routing Layer (`backend/app/api/v1/auth.py`)

- `POST /api/v1/auth/login`: Accepts credentials, logs in, registers session, returns token responses.
- `POST /api/v1/auth/logout`: Revokes active refresh token.
- `POST /api/v1/auth/refresh`: Accepts refresh token, revokes it, and yields new access/refresh pair.
- `GET /api/v1/auth/me`: Fetches current user profile and permission list.
- `POST /api/v1/auth/change-password`: Modifies password hash and revokes all active sessions.
- `POST /api/v1/auth/validate`: Endpoint for third-party service token validations.
- `GET /api/v1/auth/roles`: Returns roles definition (Admin only).
- `GET /api/v1/auth/permissions`: Returns permissions list (Admin only).

---

## 5. Frontend Components

- **`AuthProvider`** (`AuthContext.tsx`): Stores token state, schedules token refreshes, tails token expirations, and shows a session expiration warning overlay when 60 seconds remain.
- **`AuthGuard`** (`AuthGuard.tsx`): Guards pages and redirects users.
- **`LoginPage`** (`login/page.tsx`): Secure login interface supporting "Remember Me" sessions.
- **`ProfilePage`** (`profile/page.tsx`): Displays user credentials, active scopes, and handles password edits.
- **`UnauthorizedPage`** (`unauthorized/page.tsx`): Explains access restrictions.
