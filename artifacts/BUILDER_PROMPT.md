## Prompt 1: Frontend Builder

**Build the complete frontend for FindMeWriter**, a role-based, accessibility-first web platform connecting visually impaired students with volunteer writers. Use **Jinja2 templates**, **Bootstrap 5** for grid/layout, **Google Fonts** for typography, and **FontAwesome** for icons. Every page must be optimized for screen readers, keyboard navigation, and include high-contrast + large-text theme toggles.

### File Structure
```
templates/
  base.html
  partials/
    navbar.html, footer.html, sidebar.html, flash_messages.html
  auth/
    register.html, login.html, forgot_password.html
  onboarding/
    student_profile.html, volunteer_profile.html, college_profile.html
  dashboard/
    student_dashboard.html, volunteer_dashboard.html, college_dashboard.html, admin_dashboard.html
  requests/
    request_form.html, request_feed.html, request_detail.html, my_requests.html
  verification/
    verification_queue.html, verification_log.html, attendance_mark.html
  complaints/
    complaint_form.html, complaint_list.html, complaint_detail.html
  helpdesk/
    chat_room.html, helpdesk_shifts.html
  admin/
    audit_logs.html, exports.html, user_management.html, moderation_queue.html
  shared/
    profile_view.html, rating_form.html, settings.html, delete_account.html
static/
  css/
    base.css, themes.css (high-contrast, large-text), dashboard.css, forms.css
  js/
    base.js, theme_toggle.js, request_feed.js, chat_socket.js, verification_scan.js,
    form_validation.js, accessibility_helpers.js, admin_exports.js
```

### Requirements

**1. Base Template & Theming**
- `base.html` must define blocks: `title`, `meta`, `styles`, `nav`, `content`, `scripts`.
- Include Bootstrap 5 CDN, Google Fonts (Inter + Atkinson Hyperlegible for low-vision users), FontAwesome 6.
- Implement a theme toggle (standard / high-contrast / large-text) persisted in `localStorage`. Use `themes.css` with CSS variables for colors and font sizes.

**2. Accessibility (Non-negotiable)**
- All forms use `aria-label`, `aria-describedby`, `role="alert"` for errors.
- Skip-to-content links, predictable focus order, visible focus indicators.
- Tables use `scope="col"` and captions; modals trap focus.
- Every interactive element must be keyboard-accessible.

**3. Auth & Onboarding Pages**
- `register.html`: Role selector (Student/Volunteer/College). Conditional fields:
  - Students/Volunteers: Aadhaar number input + Aadhaar photocopy upload (with `accept="image/*,application/pdf"`).
  - Colleges: Institution name, affiliation code, admin contact.
- `login.html`: Role-aware redirect hint.
- Profile completion pages per role with public ID display (`student_id`, `volunteer_id`, `college_id`).

**4. Dashboards**
- **Student**: Active requests, assigned volunteer cards with contact/message buttons, complaint status, profile completion progress.
- **Volunteer**: Available request feed (geolocation badges, filter sidebar), committed/backed-up request cards, verification tasks, help desk shift signup.
- **College**: Posted requests with writer counts, verification queue (volunteer Aadhaar check interface), attendance logs, complaint handling inbox.
- **Admin**: Platform overview cards (counts, pending complaints), audit log viewer (paginated, filterable), user management table, moderation queue, export buttons (CSV/JSON).

**5. Request & Matching Flow**
- `request_form.html`: Accessible date/time pickers, location input, language select, duration, number of writers, special needs textarea.
- `request_feed.html`: Card-based layout (Bootstrap grid). Each card shows date, location, language, duration, action buttons ("Commit as Primary", "Commit as Backup", "Message"). Filter sidebar by city/language/date.
- `request_detail.html`: Full request info, committed volunteers list, backup list, status badge.

**6. Verification & Attendance**
- `verification_queue.html`: College interface. Side-by-side view: uploaded Aadhaar copy (image) vs. physical Aadhaar details form. Checkbox "Physical Aadhaar matches uploaded copy." Submit logs result.
- `attendance_mark.html`: Simple toggle buttons per volunteer (Present / Absent) with timestamp auto-fill.

**7. ComplaintBox**
- `complaint_form.html`: Complainant role auto-filled. Target role dropdown. Target ID input (validated against public IDs). Description textarea. File upload for attachments.
- `complaint_list.html`: Status badges (Open / Under Review / Resolved). Admin sees action buttons.
- `complaint_detail.html`: Thread view with admin notes and audit trail.

**8. Help Desk (Real-time Chat)**
- `chat_room.html`: Two-panel layout: volunteer list (online/offline status) and chat area. Message bubbles with `aria-live="polite"` region for new messages.
- Socket.io client connection in `chat_socket.js` with reconnection logic.
- `helpdesk_shifts.html`: Volunteer opt-in rota table with time slots.

**9. Shared Components**
- `profile_view.html`: Public profile with trust signals (rating stars, completed exams), public ID prominently displayed.
- `rating_form.html`: Post-exam feedback: 1-5 star rating (accessible), textarea, submit.
- `delete_account.html`: Confirmation flow with typed confirmation ("delete my account"), explanation of logical deletion.

**10. JavaScript Modules**
- `request_feed.js`: Dynamic filtering, geolocation sort, commit/backup AJAX with loading spinners.
- `verification_scan.js`: Image preview for uploaded Aadhaar, form validation.
- `admin_exports.js`: Trigger export downloads, show progress.
- `accessibility_helpers.js`: Font size adjuster, focus manager for SPA-like sections.

**Deliverables:** All HTML files, CSS files, and JS files. Ensure every template extends `base.html`. Use Bootstrap grid classes (`container`, `row`, `col-md-*`) consistently. No backend logic—just templated structure, forms with correct `name` attributes, and placeholder data loops (`{% for item in items %}`).

---

## Prompt 2: Backend Builder

**Build the complete backend for FindMeWriter** using **Python (Flask)**, **SQLite3**, and a modular file structure. Implement RESTful APIs, WebSocket (Flask-SocketIO) for real-time help desk chat, JWT-based role authentication, tamper-evident audit logging, and encrypted file storage for Aadhaar documents.

### File Structure
```
app.py              # App factory, config, route registration
wsgi.py             # Entry point: from app import create_app; app = create_app()
middleware/
  __init__.py
  auth.py           # JWT handling, role guards, MFA for admin
  audit.py          # Audit log decorator and writer
  encryption.py     # File encryption/decryption for Aadhaar storage
  validators.py     # Input validation (Aadhaar format, IDs, etc.)
  error_handlers.py # Custom error responses
  rate_limiter.py   # Basic rate limiting
routes/
  __init__.py
  auth.py           # Register, login, logout, profile completion
  student.py        # Student dashboard, request CRUD
  volunteer.py      # Volunteer feed, commit/backup flows
  college.py        # College requests, verification, attendance
  admin.py          # Admin dashboard, exports, moderation, audit logs
  complaints.py     # ComplaintBox endpoints
  helpdesk.py       # SocketIO events and chat history
  shared.py         # Profile, ratings, settings, delete account
models/
  db.py             # SQLite connection factory, schema init
  schema.sql        # Full database schema
utils/
  id_generator.py   # Public ID generators (student_id, etc.)
  exporters.py      # CSV/JSON export generators
config.py           # Environment-based config
```

### Requirements

**1. Database (SQLite3)**
- `schema.sql` must implement the full data model:
  - `users`: `id`, `role` (student/volunteer/college/admin), `email`, `password_hash`, `name`, `phone`, `status` (active/deactivated), `created_at`.
  - `students`: `user_id`, `student_id` (public), `aadhaar_number_hash`, `aadhaar_copy_path`, `institution`, `accessibility_needs`.
  - `volunteers`: `user_id`, `volunteer_id` (public), `aadhaar_number_hash`, `aadhaar_copy_path`, `city`, `languages`, `rating_avg`.
  - `colleges`: `user_id`, `college_id` (public), `institution_name`, `affiliation_code`, `address`.
  - `requests`: `request_id`, `created_by`, `creator_role`, `date`, `time`, `location`, `language`, `duration`, `num_writers`, `special_needs`, `status` (open/filled/completed/cancelled).
  - `commitments`: `commitment_id`, `request_id`, `volunteer_id`, `role` (primary/backup), `status`, `created_at`.
  - `verifications`: `verification_id`, `request_id`, `volunteer_id`, `college_id`, `verified_by_user_id`, `physical_match` (bool), `timestamp`, `notes`.
  - `complaints`: `complaint_id`, `complainant_id`, `target_id`, `target_role`, `description`, `attachments_json`, `status`, `admin_notes`, `created_at`, `resolved_at`.
  - `audit_logs`: `log_id`, `action`, `actor_id`, `actor_role`, `target_id`, `details_json`, `timestamp`, `hash` (tamper-evident).
  - `ratings`: `rating_id`, `request_id`, `from_id`, `to_id`, `score`, `feedback`, `created_at`.
  - `helpdesk_messages`: `message_id`, `room_id`, `sender_id`, `sender_role`, `message`, `timestamp`.
- Use `db.py` with connection pooling (`sqlite3.Row` factory) and `init_db()` command.
- All tables use foreign keys with `ON DELETE`/`ON UPDATE` rules.

**2. Authentication & Authorization (`middleware/auth.py`)**
- Register: Hash passwords with bcrypt. Validate Aadhaar format (12 digits). Store Aadhaar number hashed (SHA-256). Save encrypted Aadhaar copies.
- Login: Issue JWT access tokens (1h) and refresh tokens. Include role in token payload.
- Role guards: Decorators `@require_role('student')`, `@require_role('volunteer')`, `@require_role('college')`, `@require_role('admin')`.
- Admin MFA: TOTP verification using `pyotp` before admin dashboard access.
- Logout: Token blacklist in SQLite (or client-side deletion with expiry check).

**3. Encryption & File Storage (`middleware/encryption.py`)**
- Encrypt Aadhaar uploads using Fernet (symmetric encryption) before saving to disk.
- Store keys securely (environment variable).
- Serve decrypted files only to authorized roles (admin/college for verification).

**4. Audit Logging (`middleware/audit.py`)**
- Decorator `@audit(action="REQUEST_CREATED")` that captures actor, target, details, and writes to `audit_logs`.
- Each log entry includes a SHA-256 hash chain (`previous_hash`) for tamper evidence.
- Admin endpoints to query and export audit logs.

**5. Core API Endpoints**

**Auth (`routes/auth.py`)**
- `POST /api/auth/register` — role-specific registration with Aadhaar upload.
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/profile` — return profile + public ID.

**Student (`routes/student.py`)**
- `POST /api/student/requests` — create writer request.
- `GET /api/student/requests` — list my requests with assigned volunteers.
- `GET /api/student/dashboard` — active requests, complaint status.

**Volunteer (`routes/volunteer.py`)**
- `GET /api/volunteer/feed` — available requests, filterable by location/language/date.
- `POST /api/volunteer/commit` — commit as primary or backup.
- `POST /api/volunteer/backup-promote` — auto-promote backup if primary cancels.
- `GET /api/volunteer/commitments` — my active/past commitments.

**College (`routes/college.py`)**
- `POST /api/college/requests` — post bulk request.
- `GET /api/college/verification-queue` — pending verifications.
- `POST /api/college/verify` — log Aadhaar match result.
- `POST /api/college/attendance` — mark present/absent.
- `GET /api/college/attendance-logs` — paginated logs.

**Complaints (`routes/complaints.py`)**
- `POST /api/complaints` — submit complaint referencing `target_id` and `target_role`.
- `GET /api/complaints` — list (role-filtered; admin sees all).
- `PUT /api/complaints/<id>` — admin update status and notes.

**Admin (`routes/admin.py`)**
- `GET /api/admin/overview` — counts, pending complaints.
- `GET /api/admin/users` — user management with status filter.
- `POST /api/admin/users/<id>/suspend` — suspend/flag account.
- `GET /api/admin/audit-logs` — filtered, paginated.
- `POST /api/admin/export` — generate CSV/JSON exports (audit, users, complaints).

**Shared (`routes/shared.py`)**
- `GET /api/profile/<public_id>` — public profile with trust signals.
- `POST /api/ratings` — submit post-exam rating.
- `PUT /api/settings` — update profile.
- `POST /api/account/delete` — logical deletion (set `status = deactivated`).

**6. Real-time Help Desk (`routes/helpdesk.py` via SocketIO)**
- Namespace `/helpdesk`.
- Events: `join_room`, `send_message`, `typing`, `escalate_to_admin`.
- Persist messages to `helpdesk_messages`.
- Broadcast to room participants; notify admin on escalation.
- Track volunteer shift status.

**7. Validation & Security (`middleware/validators.py`)**
- Aadhaar: 12 digits, checksum optional.
- Public IDs: format validation (`STU-XXXX`, `VOL-XXXX`, `CLG-XXXX`).
- SQL injection prevention via parameterized queries exclusively.
- XSS protection via Jinja2 auto-escaping and input sanitization.

**8. Error Handling & Rate Limiting**
- `middleware/error_handlers.py`: JSON error responses with consistent structure (`{error, message, code}`).
- `middleware/rate_limiter.py`: In-memory rate limiting on auth endpoints (5 attempts / 15 min).

**9. WSGI & App Factory**
- `app.py`: `create_app(config_name)` factory pattern. Register blueprints. Initialize SocketIO. Enable CORS if needed.
- `wsgi.py`: Production entry point.
- `config.py`: Development, testing, production configs with secret keys, DB paths, encryption keys.

**10. Utilities**
- `utils/id_generator.py`: Generate unique public IDs (`student_id`, `volunteer_id`, `college_id`).
- `utils/exporters.py`: Stream CSV/JSON generators for large datasets to avoid memory issues.

**Deliverables:** All Python files, `schema.sql`, and `config.py`. Ensure all routes return JSON. Use SQLite transactions for multi-step operations (commit/backup promotion, verification + attendance). Include tamper-evident audit logging on every mutating action. Logical deletion must preserve historical records and public IDs in foreign tables.
