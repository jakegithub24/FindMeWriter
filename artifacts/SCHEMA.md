# SCHEMA.md — Database Schema Documentation

## 1. Entity Relationship Overview
```
users ||--o{ students : "1:1"
users ||--o{ volunteers : "1:1"
users ||--o{ colleges : "1:1"
users ||--o{ requests : "creates"
users ||--o{ complaints : "files"
users ||--o{ audit_logs : "performs"

students ||--o{ requests : "creates"
colleges ||--o{ requests : "creates"

requests ||--o{ commitments : "has"
volunteers ||--o{ commitments : "makes"

requests ||--o{ verifications : "logged for"
volunteers ||--o{ verifications : "subject of"
colleges ||--o{ verifications : "performed by"

requests ||--o{ ratings : "receives"
users ||--o{ ratings : "gives/receives"

users ||--o{ helpdesk_messages : "sends"
```

## 2. Table Definitions

### `users`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, AUTOINCREMENT | Internal ID |
| `role` | TEXT | NOT NULL, CHECK IN ('student','volunteer','college','admin') | |
| `email` | TEXT | UNIQUE, NOT NULL | Login identifier |
| `password_hash` | TEXT | NOT NULL | bcrypt hash |
| `name` | TEXT | NOT NULL | Display name |
| `phone` | TEXT | | Contact number |
| `status` | TEXT | DEFAULT 'active', CHECK IN ('active','deactivated') | Logical deletion |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

### `students`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `user_id` | INTEGER | PK, FK → users.id ON DELETE CASCADE | |
| `student_id` | TEXT | UNIQUE, NOT NULL | Public ID (e.g., STU-7A3F) |
| `aadhaar_number_hash` | TEXT | NOT NULL | SHA-256 of 12-digit number |
| `aadhaar_copy_path` | TEXT | NOT NULL | Encrypted file path |
| `institution` | TEXT | | Current school/college |
| `accessibility_needs` | TEXT | | Screen reader, scribe preference, etc. |

### `volunteers`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `user_id` | INTEGER | PK, FK → users.id ON DELETE CASCADE | |
| `volunteer_id` | TEXT | UNIQUE, NOT NULL | Public ID (e.g., VOL-9B2E) |
| `aadhaar_number_hash` | TEXT | NOT NULL | SHA-256 |
| `aadhaar_copy_path` | TEXT | NOT NULL | Encrypted file path |
| `city` | TEXT | | Primary location |
| `languages` | TEXT | | Comma-separated |
| `rating_avg` | REAL | DEFAULT 0.0 | 0.0–5.0 |
| `total_exams` | INTEGER | DEFAULT 0 | |

### `colleges`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `user_id` | INTEGER | PK, FK → users.id ON DELETE CASCADE | |
| `college_id` | TEXT | UNIQUE, NOT NULL | Public ID (e.g., CLG-4C1D) |
| `institution_name` | TEXT | NOT NULL | |
| `affiliation_code` | TEXT | | University/board code |
| `address` | TEXT | | Full address |

### `requests`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `request_id` | INTEGER | PK, AUTOINCREMENT | |
| `created_by` | INTEGER | FK → users.id | |
| `creator_role` | TEXT | NOT NULL | 'student' or 'college' |
| `date` | DATE | NOT NULL | Exam date |
| `time` | TIME | NOT NULL | Exam start time |
| `location` | TEXT | NOT NULL | Exam center address |
| `language` | TEXT | NOT NULL | Language of exam |
| `duration` | INTEGER | NOT NULL | Minutes |
| `num_writers` | INTEGER | DEFAULT 1 | |
| `special_needs` | TEXT | | Accessibility requirements |
| `status` | TEXT | DEFAULT 'open', CHECK IN ('open','filled','completed','cancelled') | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

### `commitments`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `commitment_id` | INTEGER | PK, AUTOINCREMENT | |
| `request_id` | INTEGER | FK → requests.request_id ON DELETE CASCADE | |
| `volunteer_id` | INTEGER | FK → volunteers.user_id | |
| `role` | TEXT | NOT NULL, CHECK IN ('primary','backup') | |
| `status` | TEXT | DEFAULT 'active', CHECK IN ('active','cancelled','fulfilled') | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

### `verifications`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `verification_id` | INTEGER | PK, AUTOINCREMENT | |
| `request_id` | INTEGER | FK → requests.request_id | |
| `volunteer_id` | INTEGER | FK → volunteers.user_id | |
| `college_id` | INTEGER | FK → colleges.user_id | |
| `verified_by_user_id` | INTEGER | FK → users.id | College staff who verified |
| `physical_match` | BOOLEAN | NOT NULL | True if Aadhaar matches |
| `timestamp` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| `notes` | TEXT | | Mismatch details |

### `complaints`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `complaint_id` | INTEGER | PK, AUTOINCREMENT | |
| `complainant_id` | INTEGER | FK → users.id | |
| `target_id` | TEXT | NOT NULL | Public ID of target |
| `target_role` | TEXT | NOT NULL | Role of target |
| `description` | TEXT | NOT NULL | |
| `attachments_json` | TEXT | DEFAULT '[]' | Array of file paths |
| `status` | TEXT | DEFAULT 'open', CHECK IN ('open','under_review','resolved') | |
| `admin_notes` | TEXT | | Resolution notes |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| `resolved_at` | TIMESTAMP | | |

### `audit_logs`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `log_id` | INTEGER | PK, AUTOINCREMENT | |
| `action` | TEXT | NOT NULL | e.g., 'REQUEST_CREATED' |
| `actor_id` | INTEGER | FK → users.id | |
| `actor_role` | TEXT | NOT NULL | |
| `target_id` | INTEGER | | Affected entity |
| `details_json` | TEXT | NOT NULL | Serialized context |
| `timestamp` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| `hash` | TEXT | NOT NULL | SHA-256 chain hash |

### `ratings`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `rating_id` | INTEGER | PK, AUTOINCREMENT | |
| `request_id` | INTEGER | FK → requests.request_id | |
| `from_id` | INTEGER | FK → users.id | Rater |
| `to_id` | INTEGER | FK → users.id | Ratee |
| `score` | INTEGER | CHECK (score >= 1 AND score <= 5) | |
| `feedback` | TEXT | | |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

### `helpdesk_messages`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `message_id` | INTEGER | PK, AUTOINCREMENT | |
| `room_id` | TEXT | NOT NULL | Chat room identifier |
| `sender_id` | INTEGER | FK → users.id | |
| `sender_role` | TEXT | NOT NULL | |
| `message` | TEXT | NOT NULL | |
| `timestamp` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

## 3. Indexes
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_date ON requests(date);
CREATE INDEX idx_commitments_volunteer ON commitments(volunteer_id);
CREATE INDEX idx_commitments_request ON commitments(request_id);
CREATE INDEX idx_verifications_request ON verifications(request_id);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_helpdesk_room ON helpdesk_messages(room_id);
```

## 4. Constraints & Rules
- **Unique Aadhaar**: `aadhaar_number_hash` must be unique across `students` and `volunteers` (enforced in application layer).
- **Public ID Uniqueness**: `student_id`, `volunteer_id`, `college_id` globally unique.
- **Status Transitions**: `requests.status` can only move: `open → filled → completed`, `open → cancelled`, `filled → open` (on cancellation).
- **Audit Immutability**: `audit_logs` rows are INSERT-only; never updated or deleted.
