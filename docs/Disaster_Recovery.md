# Disaster Recovery Plan

This document outlines recovery procedures during critical failures (data corruption, server crash).

---

## 1. Database Corruption Recovery

If SQLite database files (`traffic_system.db`) become corrupt:

1. Stop application containers:
   ```bash
   docker compose -f deployment/docker-compose.production.yml stop backend
   ```
2. Locate the latest backup in `/backups` (e.g. `db_20260709_120000.tar.gz`).
3. Run the recovery restore script inside the environment:
   ```bash
   ./deployment/docker/scripts/restore.sh 20260709_120000
   ```
4. Restart application containers:
   ```bash
   docker compose -f deployment/docker-compose.production.yml start backend
   ```

---

## 2. Server Failover

In case of hardware failure:

1. Provision a new server instance.
2. Clone repository and copy latest files from `/backups` partition.
3. Build and launch:
   ```bash
   docker compose -f deployment/docker-compose.production.yml up -d
   ```
