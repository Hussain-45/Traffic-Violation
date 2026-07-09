# System Maintenance Guide

Routine updates, backups scheduling, and scaling procedures.

---

## 1. Scheduling Daily Backups

Set up a cron job on the host machine to execute `backup.sh` daily at midnight:

1. Edit crontab:
   ```bash
   crontab -e
   ```
2. Append the backup task instruction:
   ```cron
   0 0 * * * /workspace/deployment/docker/scripts/backup.sh >> /var/log/backup_cron.log 2>&1
   ```

---

## 2. Upgrading Container Application

Deploy new releases with minimal downtime:

1. Fetch latest changes:
   ```bash
   git pull origin main
   ```
2. Rebuild and restart:
   ```bash
   docker compose -f deployment/docker-compose.production.yml up -d --build
   ```
3. Prune old layers:
   ```bash
   docker image prune -f
   ```
