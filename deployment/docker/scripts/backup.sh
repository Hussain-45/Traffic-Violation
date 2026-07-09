#!/bin/bash
# ==============================================================================
# Production Backup Script
# ==============================================================================
# Backs up databases, uploads/evidence files, and system configs. Keeps last 7 logs.
# ==============================================================================

BACKUP_DIR="/backups"
DATA_DIR="/workspace/data"
CONFIG_DIR="/workspace/configs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "[$(date)] Starting STVDS production backups..."
mkdir -p "$BACKUP_DIR"

# 1. Archive databases
echo "[$(date)] Backing up SQLite databases..."
tar -czf "$BACKUP_DIR/db_$TIMESTAMP.tar.gz" -C "$DATA_DIR" ./traffic_system.db ./test_reports.db ./test_analytics.db 2>/dev/null

# 2. Archive uploads & evidence files
echo "[$(date)] Backing up uploaded evidence files (images/videos)..."
tar -czf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" -C "$DATA_DIR" ./uploads 2>/dev/null

# 3. Archive system configurations
echo "[$(date)] Backing up configs..."
tar -czf "$BACKUP_DIR/configs_$TIMESTAMP.tar.gz" -C "$CONFIG_DIR" . 2>/dev/null

# 4. Enforce 7-day rotation policy
echo "[$(date)] Rotating older backups (keeping latest 7 files of each group)..."
find "$BACKUP_DIR" -name "db_*.tar.gz" -type f | sort -r | tail -n +8 | xargs rm -f 2>/dev/null
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -type f | sort -r | tail -n +8 | xargs rm -f 2>/dev/null
find "$BACKUP_DIR" -name "configs_*.tar.gz" -type f | sort -r | tail -n +8 | xargs rm -f 2>/dev/null

# 5. Generate checksum verification values
echo "[$(date)] Generating SHA256 verification checksums..."
sha256sum "$BACKUP_DIR/db_$TIMESTAMP.tar.gz" > "$BACKUP_DIR/db_$TIMESTAMP.tar.gz.sha256" 2>/dev/null
sha256sum "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" > "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz.sha256" 2>/dev/null
sha256sum "$BACKUP_DIR/configs_$TIMESTAMP.tar.gz" > "$BACKUP_DIR/configs_$TIMESTAMP.tar.gz.sha256" 2>/dev/null

echo "[$(date)] Production backup completed successfully."
