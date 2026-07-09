# Deployment Guide

This document describes how to deploy the Traffic Violation AI platform to production environments using Docker and Nginx.

---

## 1. System Architecture

The production environment is packaged inside isolated Docker containers:

- **Proxy Layer (Nginx)**: Port 80 (HTTP) and 443 (HTTPS). Routes traffic, terminates SSL/TLS, applies rate limits, and compresses text assets.
- **Frontend Layer**: Static React/Next.js bundle compiled during Docker build.
- **Backend Layer**: FastAPI web server running via Uvicorn with 4 workers.
- **Storage Layer**: Persistent Docker local volume mount `/workspace/data` containing the sqlite databases and uploads media.

---

## 2. Docker Containers Setup

### 2.1 Build Production Images
Build and package the containers:
```bash
docker compose -f deployment/docker-compose.production.yml build
```

### 2.2 Run Production Containers
Spin up the platform in detached mode:
```bash
docker compose -f deployment/docker-compose.production.yml up -d
```

---

## 3. Environment Isolation

Configure `.env.production` in root directory:
```env
ENV_STATE=production
DATABASE_URL=sqlite:///data/traffic_system.db
JWT_SECRET_KEY=super-secret-production-hash-key
JWT_REFRESH_SECRET_KEY=super-secret-refresh-hash-key
UPLOAD_DIR=data/uploads
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

Startup validation ensures that if any variables are missing in production mode, the application immediately prints warnings and halts to prevent security leakage.
