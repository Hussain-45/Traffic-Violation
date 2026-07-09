#!/bin/bash
# ==============================================================================
# Production Restore Script
# ==============================================================================
# Restores databases, uploads/evidence files, and configs from a specified timestamp.
# Usage: ./restore.sh <TIMESTAMP_YYYYMMDD_HHMMSS>
# ==============================================================================

BACKUP_DIR="/backups"
DATA_DIR="/workspace/data"
CONFIG_DIR="/workspace/configs"
TIMESTAMP=$1

if [ -z "$TIMESTAMP" ]; then
    echo "CRITICAL: Missing backup timestamp parameter."
    echo "Usage: ./restore.sh <TIMESTAMP_YYYYMMDD_HHMMSS>"
    exit 1
fi

echo "[$(date)] Starting STVDS production recovery..."

# Verify backup files exist
if [ ! -f "$BACKUP_DIR/db_$TIMESTAMP.tar.gz" ] || [ ! -f "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" ] || [ ! -f "$BACKUP_DIR/configs_$TIMESTAMP.tar.gz" ]; then
    echo "CRITICAL: One or more backup files for timestamp $TIMESTAMP not found in $BACKUP_DIR."
    exit 1
fi

# 1. Restore databases
echo "[$(date)] Restoring SQLite databases..."
tar -xzf "$BACKUP_DIR/db_$TIMESTAMP.tar.gz" -C "$DATA_DIR"

# 2. Restore uploads & evidence files
echo "[$(date)] Restoring uploaded evidence files..."
tar -xzf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" -C "$DATA_DIR"

# 3. Restore configs
echo "[$(date)] Restoring configurations..."
tar -xzf "$BACKUP_DIR/configs_$TIMESTAMP.tar.gz" -C "$CONFIG_DIR"

echo "[$(date)] Production restore completed successfully."
