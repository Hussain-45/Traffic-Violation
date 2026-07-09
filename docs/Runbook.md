# Operational Runbook

Operational procedures, commands, and troubleshooting guidelines for the Traffic Violation AI platform.

---

## 1. System Operations

### 1.1 Startup Platform
```bash
docker compose -f deployment/docker-compose.production.yml up -d
```

### 1.2 Stop Platform
```bash
docker compose -f deployment/docker-compose.production.yml down
```

---

## 2. Logs Monitoring

### 2.1 View Backend Service Logs
```bash
docker logs -f stvds-prod-backend
```

### 2.2 View Nginx Proxy logs
```bash
docker logs -f stvds-prod-proxy
```

---

## 3. Health & Diagnostics

Access the diagnostic endpoints using cURL:
```bash
curl -f http://localhost:8000/api/v1/admin/health
```
Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "smtp": "active",
  "storage": "normal"
}
```
