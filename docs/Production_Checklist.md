# Production Readiness Checklist

Verify all items on this list before releasing Traffic Violation AI platform v1.0.0.

---

## 1. Security Compliance

- [ ] **SSL/TLS Certificates**: Setup certs and configure Nginx port 443 with modern TLS protocols (v1.2, v1.3).
- [ ] **Secret Management**: Ensure all production secrets are injected via system environment variables rather than hardcoded.
- [ ] **Rate Limiting**: Nginx zone `api_limit` configured to restrict requests to `10r/s` with a burst of `20`.
- [ ] **Account Lockouts**: Validate user lockouts trigger after 5 consecutive failed login attempts.
- [ ] **Password Strength**: Confirm password updates adhere to lengths and complexity (uppercase, digits, special characters).

---

## 2. Infrastructure & Storage

- [ ] **Docker Volumes**: Verify database files (`traffic_system.db`) and uploaded media are saved on persistent Docker volumes.
- [ ] **Log Rotation**: Configure logrotate daemon templates on the host machine.
- [ ] **Database Connection Pool**: Set connection pool limits.

---

## 3. Backups & Monitoring

- [ ] **Automated Backups**: Test backup script `backup.sh` runs successfully.
- [ ] **Recovery Drills**: Run restore script `restore.sh` to verify databases recovery.
- [ ] **Health Checks**: Access and test `/api/v1/admin/health` diagnostics API.
