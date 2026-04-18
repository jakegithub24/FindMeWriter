# FindMeWriter

## Overview
FindMeWriter is a non-profit, community-driven, open-source platform (GPL v3.0) that connects visually impaired students and exam-conducting colleges with verified volunteer writers. It centralizes matching, verification, scheduling, incident handling, and realtime help so students can focus on exams.

## Goals
- Ensure visually impaired students reliably obtain verified writers for written exams.
- Give colleges auditable verification and contingency workflows.
- Build a transparent, accessible, volunteer-powered ecosystem governed in the open.

## High-level Architecture
- Role-based web app (Student, College, Volunteer, Admin).
- Real-time layer (WebSockets) for notifications and volunteer-driven Help Desk chat.
- Encrypted storage for identity documents and tamper-evident audit logs.
- Public GitHub repo under GPL v3.0 for code, docs, and contributions.

## Core Features

### Role-based Onboarding & Identity
- Students, Volunteers, and Colleges create role-specific profiles.
- Required identity linkage:
  - Students and Volunteers must upload a photocopy of their Aadhaar and enter Aadhaar number at registration.
  - Colleges provide institutional details and coordinate with admin for bulk/verified registrations where needed.
- Unique public identifiers:
  - student_id, volunteer_id, college_id — shown on profiles and used in ComplaintBox and reporting to tag parties.
- Aadhaar linkage prevents duplicate personal profiles; platform stores Aadhaar copies securely and links to IDs.

### Requests & Matching
- "Writer needed" requests by Students (single writer) and Colleges (one or many writers).
- Structured fields: date/time, location, duration, language, number of writers, special instructions, accessibility needs.
- Volunteer feed: geolocation and filter prioritized list of request cards with action buttons (Commit, Backup, Message).
- Commit/backup flow with automatic backup promotion on cancellation.

### Verification, Attendance & Audit
- Volunteer must present physical Aadhaar at exam center; college verifies against uploaded copy and logs result.
- Colleges mark attendance (present/absent) and verification outcome; logs are tamper-evident.
- Admin can export logs (CSV/JSON) for investigations; exports include immutable audit trails.

### ComplaintBox & Moderation
- Any role may submit complaints about platform issues or another user (student/college/volunteer).
- Complaints must reference public IDs (student_id, volunteer_id, college_id) to ensure traceability.
- Admin triages complaints, can suspend/flag accounts, and record outcomes in audit logs.

### Help Desk (Volunteer-driven)
- Realtime chat (socket connection) staffed by volunteers for live support and escalation to admin.
- Chat integrates with notifications and incident logging; help desk volunteers operate in shifts/rotas.

### Dashboards & UX
- Role-specific dashboards:
  - Students: active requests, assigned volunteers, complaint status, profile.
  - Colleges: posted requests, verification queue, attendance logs, complaint handling.
  - Volunteers: available requests, commitments/backups, verification tasks, help desk shifts.
  - Admin: platform overview, audits, exports, moderation tools.
- Accessibility-first design:
  - Assisted, form-based flows optimized for screen readers and keyboard navigation.
  - ARIA roles, predictable focus order, high contrast and large-text themes.

### Account Lifecycle & Data Retention
- Logical deletion:
  - Students, Colleges, and Volunteers may request account deletion (logical/deactivate).
  - Logical deletion hides profile and prevents new actions but preserves historical logs, audits, verification records, and exported data for the admin.
- Admin retains access to past records for compliance, dispute resolution, and audits.

### Trust & Reputation
- Post-exam ratings and feedback per engagement.
- Trust signals surface reliable volunteers and flag repeat issues for moderation.

## Compliance & Data Security Considerations
- Aadhaar and identity documents stored encrypted at rest with strict access control; minimal retention policy and defined deletion/archival procedures in line with applicable laws.
- Role-based access control and admin MFA.
- Tamper-evident audit logs and export history for accountability.
- Legal review recommended before launch for Aadhaar handling and local data-protection compliance.

## Suggested Technology Stack (example)
- Frontend: React with an ARIA-first component library; automated accessibility testing.
- Backend: Node.js/Express or Python/FastAPI; REST + WebSocket endpoints.
- Realtime: socket.io or native WebSockets for help desk and notifications.
- DB: PostgreSQL for primary data + audit tables; Redis for pub/sub and ephemeral states.
- Storage: Encrypted object storage for ID docs; secure key management.
- Auth: Role-based JWT; strong admin MFA.
- CI/CD: GitHub Actions; containerized deployment.
- License: GPL v3.0 (repo, contribution guide, code of conduct).

## Data Model (high level)
- Users: { id, role, name, contact, student_id/volunteer_id/college_id, aadhaar_hash, aadhaar_copy_reference, status }
- Requests: { request_id, created_by, type (student/college), date, time, location, language, duration, num_writers, special_needs, status }
- Commitments: { commitment_id, request_id, volunteer_id, role (primary/backup), status, timestamp }
- Verifications: { verification_id, request_id, volunteer_id, college_id, verified_by, physical_match (bool), timestamp, notes }
- Complaints: { complaint_id, complainant_id, target_id, target_role, description, attachments, status, admin_notes }
- AuditLogs: immutable entries for key actions (uploads, verifications, deletions, exports).

## Workflows

### Student Registration & Request
1. Register → upload Aadhaar copy, enter Aadhaar number → receive student_id.
2. Complete accessibility-assisted form to create "Writer needed" request.
3. Track commitments, communicate with volunteer, submit feedback or complaints.

### Volunteer Registration & Commit
1. Register → upload Aadhaar copy, enter Aadhaar number → receive volunteer_id.
2. Browse feed, commit as primary or backup.
3. Attend exam with physical Aadhaar; college verifies and logs attendance.

### College Posting & Verification
1. Create institutional profile and coordinate with admin if special setup needed.
2. Post request(s) with required number of writers.
3. Verify volunteer physical Aadhaar against uploaded copy and record verification result.

### Help Desk Operation
1. Volunteers opt-in to help desk rota.
2. Users open realtime chat; help desk volunteers assist via socket connection and log incidents.
3. Escalate unresolved issues to admin via ComplaintBox or moderation queue.

### Complaint Handling
1. Submit complaint referencing public IDs (student_id/volunteer_id/college_id).
2. Admin reviews complaint, accesses relevant audit logs, takes action, and records outcome.

### Account Deletion (Logical)
1. User requests deletion → system marks account as deactivated (logical delete).
2. Public identifiers remain in audit logs; admin retains export and historical access.
3. Reactivation only via admin (if policy permits).

## Operational Recommendations & Launch Plan
1. Build an MVP including:
   - Role-based signup with Aadhaar upload, student/college/volunteer IDs.
   - Request posting, commit/backup flows, verification logging.
   - Realtime notification + volunteer-driven help desk chat.
   - ComplaintBox and admin audit/export tools.
   - Accessibility-first UI.
2. Conduct legal review for Aadhaar handling and data-retention policies.
3. Pilot with a small set of colleges and volunteers; run accessibility audits and iterate.
4. Publish repository, contribution guidelines, and community governance; onboard moderators and help-desk volunteers.
5. Expand after incorporating pilot feedback and compliance sign-off.

## Governance & Community
- GPL v3.0 license for the codebase.
- Clear contribution guide, issue tracker, test matrix, and code of conduct.
- Roles for maintainers, accessibility reviewers, legal/compliance advisors, and community moderators.
- Encourage contributions from students, colleges, volunteers, developers, accessibility experts, and testers.

## Impact
- Reduces access barriers and administrative friction for visually impaired students.
- Provides colleges with auditable verification and reliable contingencies.
- Builds a scalable, transparent volunteer ecosystem that increases exam access equity.
