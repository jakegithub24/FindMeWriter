# TRD.md — Technical Requirements Document

## 1. Architecture Overview
Three-tier web application:
- **Presentation**: Server-rendered Jinja2 templates + Bootstrap 5 + vanilla JS
- **Application**: Flask (Python) REST API + SocketIO real-time layer
- **Data**: SQLite3 (primary + audit tables) + encrypted filesystem storage

## 2. Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Frontend | Jinja2, Bootstrap 5, Google Fonts, FontAwesome | Rapid development, accessible defaults, no build step |
| Backend | Python 3.11+, Flask, Flask-SocketIO | Lightweight, mature ecosystem, easy WebSocket integration |
| Database | SQLite3 | Zero-config, portable, sufficient for MVP scale |
| Realtime | SocketIO | Fallback transport, room-based chat, event-driven |
| Auth | bcrypt, PyJWT, pyotp | Secure password hashing, stateless tokens, TOTP for admin |
| Encryption | cryptography (Fernet) | Symmetric encryption for Aadhaar documents |
| Audit | SHA-256 hash chain | Tamper-evident log integrity |
| CI/CD | GitHub Actions, Docker | Automated testing, containerized deployment |
| License | GPL v3.0 | Open-source compliance |

## 3. API & Endpoint Specifications

### 3.1 Authentication
- `POST /api/auth/register` — multipart/form-data (profile + Aadhaar file)
- `POST /api/auth/login` → `{access_token, refresh_token, role}`
- `POST /api/auth/refresh`
- `GET /api/auth/profile`

### 3.2 Core Resources
- `GET|POST /api/student/requests`
- `GET|POST /api/volunteer/feed`
- `POST /api/volunteer/commit`
- `GET|POST /api/college/requests`
- `POST /api/college/verify`
- `POST /api/college/attendance`
- `POST /api/complaints`
- `GET /api/admin/audit-logs`
- `POST /api/admin/export`

### 3.3 WebSocket Events (Namespace `/helpdesk`)
- `join_room` {room_id}
- `send_message` {room_id, message, sender_id}
- `typing` {room_id, sender_id}
- `escalate_to_admin` {room_id, reason}

## 4. Security Requirements
- **SEC-1**: All passwords hashed with bcrypt (cost factor 12).
- **SEC-2**: Aadhaar numbers stored as SHA-256 hashes; photocopies encrypted with Fernet.
- **SEC-3**: Encryption key stored in environment variable only.
- **SEC-4**: JWT access tokens expire in 1 hour; refresh tokens in 7 days.
- **SEC-5**: Admin endpoints require valid TOTP code in `X-Admin-MFA` header.
- **SEC-6**: Rate limiting on auth endpoints: 5 requests per 15 minutes per IP.
- **SEC-7**: All SQL queries parameterized; zero string concatenation.
- **SEC-8**: CORS restricted to known origins in production.

## 5. Performance & Scalability
- Connection pooling for SQLite via `sqlite3` module.
- Pagination on all list endpoints (default 20, max 100).
- Indexed columns: `users.email`, `requests.status`, `commitments.volunteer_id`, `audit_logs.timestamp`.
- File uploads capped at 5MB; served via authenticated routes only.

## 6. Data Retention & Compliance
- Aadhaar copies retained only as long as user account is active + 1 year archival.
- Logical deletion preserves `audit_logs`, `verifications`, `complaints` indefinitely.
- Export history logged in audit trail.

## 7. Deployment Architecture
- Containerized via Docker.
- Reverse proxy (Nginx) handles TLS termination and static file serving.
- SQLite volume mounted for persistence.
- Environment-based configuration (`development`, `testing`, `production`).
