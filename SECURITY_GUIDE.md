# 🔐 Security Best Practices Guide - Kloq Ride Dashboard

## For Developers & Administrators

---

## 1. Environment Variables & Secrets Management

### ✅ DO:
```python
# Load from environment
email = os.getenv('ADMIN_EMAIL')
password = os.getenv('ADMIN_PASSWORD')
```

### ❌ DON'T:
```python
# Hardcode credentials
USERS = {
    "admin@kloqride.com": {"password": "admin123"}  # NEVER!
}
```

### .gitignore Setup:
```
# Hide all environment files with real secrets
.env
.env.local
.env.*.local
config/secrets.*
```

---

## 2. Session Security

### Session Timeout Settings:
```
# Short sessions for public/shared devices
SESSION_TIMEOUT_MINUTES=5

# Medium sessions for office dashboards
SESSION_TIMEOUT_MINUTES=30

# Longer sessions for personal admin access
SESSION_TIMEOUT_MINUTES=480  # 8 hours
```

### What Happens on Timeout:
- User is automatically logged out
- Warning message displayed
- Session state is completely cleared
- User must re-enter credentials

---

## 3. Password Security

### Current (Demo):
- Plain text passwords in `.env`
- Acceptable for development/demo only

### For Production:
```python
import bcrypt

# Hash password on storage
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Verify on login
is_valid = bcrypt.checkpw(password.encode(), hashed)
```

### Never:
- Store passwords in code
- Use reversible encryption
- Log passwords
- Send passwords in URLs/logs

---

## 4. Data Persistence Security

### Current Implementation:
- JSON files in `./data/` directory
- No encryption at rest
- Good for demo/development

### For Production:
Use encrypted database:
```python
from sqlalchemy import create_engine
from sqlalchemy_utils import EncryptedType

# Example: PostgreSQL with encryption
engine = create_engine('postgresql://user:pass@localhost/kloq')
```

### File Permissions:
```bash
# Restrict data directory access (Linux/Mac)
chmod 700 ./data
chmod 600 ./data/*

# On Windows, use NTFS permissions:
# - Remove inherited permissions
# - Grant access only to app user
```

---

## 5. Authentication & Authorization

### Current:
- Role-based (Admin, Operations, Driver)
- Simple demo implementation

### Missing (Add for Production):
```python
@require_role(['Admin', 'Operations'])
def admin_function():
    # Only Admin and Ops can access
    pass

@require_admin_only
def dangerous_operation():
    # Only Admin
    pass
```

---

## 6. Data Validation & Input Sanitization

### Currently Implemented:
```python
# Phone number validation
if phone in existing_phones:
    st.warning("Phone already exists")

# Required fields
if not name or not phone or not vehicle:
    st.error("Fill all required fields")
```

### Add for Production:
```python
import re
from email_validator import validate_email

# Email validation
try:
    validate_email(email)
except:
    raise ValueError("Invalid email")

# Phone validation
if not re.match(r'^\d{10}$', phone):
    raise ValueError("Invalid phone format")

# SQL Injection prevention
# Use parameterized queries (SQLAlchemy handles this)
query = User.query.filter_by(email=email)  # ✅ Safe
```

---

## 7. API Security (When Adding APIs)

### CORS Configuration:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # ✅ Specific
    # DON'T allow_origins=["*"]  # ❌ Dangerous
)
```

### API Authentication:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/drivers")
async def get_drivers(credentials: HTTPAuthenticationCredentials = Depends(security)):
    token = credentials.credentials
    # Verify token...
    return drivers
```

---

## 8. Logging & Monitoring

### Current:
- Error messages shown to users
- No audit logging

### For Production - Add:
```python
import logging

logger = logging.getLogger(__name__)
logger.handlers = []  # Remove default handlers

# Log to file
fh = logging.FileHandler('kloqride.log')
fh.setLevel(logging.WARNING)

# Don't log passwords/sensitive data
logger.info(f"User login: {user_email}")  # ✅
# logger.info(f"Login: {email}:{password}")  # ❌
```

### Audit Trail Example:
```python
# Every change logged with timestamp, user, action
audit_log = {
    "timestamp": datetime.now(),
    "user": user_email,
    "action": "delete_driver",
    "target": "Ravi Kumar",
    "status": "success"
}
save_data("audit_logs.json", audit_log)
```

---

## 9. File Upload Security

### Current:
- Accepts JPG, PNG, PDF
- No size limits
- No virus scanning

### Add for Production:
```python
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_upload(file):
    # Check file size
    if len(file.getvalue()) > MAX_FILE_SIZE:
        raise ValueError("File too large")
    
    # Check file type by magic bytes, not extension
    import magic
    mime = magic.from_buffer(file.getvalue(), mime=True)
    if mime not in ['image/jpeg', 'image/png', 'application/pdf']:
        raise ValueError("Invalid file type")
    
    # Virus scan
    import clamd
    clam = clamd.ClamD()
    if clam.scan_stream(file.getvalue())['stream'][0] == 'FOUND':
        raise ValueError("Malware detected!")
    
    return True
```

---

## 10. HTTPS & Transport Security

### Development:
```bash
streamlit run app.py  # HTTP is OK locally
```

### Production:
```bash
# Always use HTTPS
# Use Let's Encrypt for free SSL certificates
certbot certonly --standalone -d yourdomain.com

# Streamlit HTTPS configuration:
streamlit run app.py --logger.level=debug \
  --client.sslCertFile=path/to/cert.pem \
  --client.sslKeyFile=path/to/key.pem
```

---

## 11. Backup & Disaster Recovery

### Daily Backups:
```bash
#!/bin/bash
# backup.sh - Run daily via cron

BACKUP_DIR="/backups/kloqride"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup data
tar -czf "$BACKUP_DIR/data_$TIMESTAMP.tar.gz" ./data/

# Keep only last 30 days
find "$BACKUP_DIR" -name "data_*.tar.gz" -mtime +30 -delete
```

### Cron Job:
```
# Run backup daily at 2 AM
0 2 * * * /path/to/backup.sh
```

---

## 12. Security Checklist for Production

- [ ] All credentials in `.env` (never in code)
- [ ] `.env` file in `.gitignore`
- [ ] Session timeout configured
- [ ] HTTPS enabled
- [ ] File uploads validated & scanned
- [ ] Input data sanitized
- [ ] Error messages don't leak info
- [ ] Logging implemented (without secrets)
- [ ] Audit trail maintained
- [ ] Database encrypted
- [ ] Regular backups scheduled
- [ ] Access logs monitored
- [ ] Database credentials secured
- [ ] API rate limiting enabled
- [ ] CORS properly configured

---

## 13. Emergency Response

### If Credentials Leaked:
```bash
# 1. Immediately rotate all passwords
# 2. Update .env file
# 3. Force logout all users
# 4. Change database passwords
# 5. Review access logs
# 6. Notify users if needed
# 7. Update documentation
```

### If Unauthorized Access Detected:
```bash
# 1. Disable affected accounts
# 2. Check audit logs for damage
# 3. Restore from clean backup
# 4. Force password reset for all users
# 5. Review and patch vulnerabilities
# 6. Document incident
```

---

## 14. Resources & References

- **OWASP Top 10**: https://owasp.org/Top10/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **Streamlit Security**: https://docs.streamlit.io/deploy/run-an-app
- **Python Security**: https://python.readthedocs.io/en/latest/library/security_warnings.html
- **SQLAlchemy Security**: https://docs.sqlalchemy.org/
- **Let's Encrypt**: https://letsencrypt.org/

---

## Quick Security Audit Script

```bash
#!/bin/bash
# Run this monthly to check security

echo "🔍 Security Audit - Kloq Ride Dashboard"
echo "========================================"

# Check for hardcoded secrets
echo "Checking for hardcoded credentials..."
grep -r "password.*=.*\"" . --include="*.py" 2>/dev/null | grep -v ".env" && echo "⚠️ FOUND HARDCODED CREDENTIALS!" || echo "✅ No hardcoded credentials"

# Check .gitignore
echo "Checking .gitignore..."
grep ".env" .gitignore > /dev/null && echo "✅ .env in .gitignore" || echo "❌ .env NOT in .gitignore!"

# Check permissions
echo "Checking data directory permissions..."
stat -f "%OLp" ./data 2>/dev/null || stat -c "%a" ./data 2>/dev/null

echo "========================================"
echo "Audit complete!"
```

---

**Remember**: Security is an ongoing process, not a one-time fix!  
**Last Updated**: April 21, 2026  
**Maintained By**: Kloq Ride Security Team
