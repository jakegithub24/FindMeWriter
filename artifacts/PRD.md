# PRD.md — Product Requirements Document

## 1. Executive Summary
**FindMeWriter** is a non-profit, open-source (GPL v3.0), community-driven platform that connects visually impaired students and examination-conducting colleges with verified volunteer writers. It centralizes writer matching, identity verification, attendance logging, real-time help desk support, and complaint moderation into a single auditable system.

## 2. Goals & Objectives
| Goal | Success Metric |
|------|---------------|
| Ensure reliable writer availability for visually impaired students | >95% request fulfillment rate |
| Provide colleges with auditable verification workflows | 100% of exams have tamper-evident logs |
| Build a transparent, volunteer-powered ecosystem | >80% volunteer retention per semester |
| Maintain accessibility-first design | WCAG 2.1 AA compliance on all screens |

## 3. Target Users (Personas)
- **Student (Visually Impaired)**: Needs screen-reader optimized flows, assisted form entry, and reliable writer assignment.
- **Volunteer Writer**: Needs a browsable request feed, one-click commitment, and clear verification instructions.
- **College Coordinator**: Needs bulk request posting, Aadhaar verification tools, and attendance export.
- **Platform Admin**: Needs audit trails, moderation queues, account suspension tools, and data exports.

## 4. Functional Requirements

### 4.1 Identity & Onboarding
- **FR-1.1**: Role-based registration (Student, Volunteer, College, Admin).
- **FR-1.2**: Students and Volunteers must upload Aadhaar photocopy and enter Aadhaar number; system prevents duplicate identity profiles.
- **FR-1.3**: Colleges provide institutional details and coordinate with admin for bulk verification.
- **FR-1.4**: System generates unique public identifiers: `student_id`, `volunteer_id`, `college_id`.

### 4.2 Request & Matching
- **FR-2.1**: Students create single-writer requests; Colleges create multi-writer requests.
- **FR-2.2**: Request fields: date, time, location, duration, language, number of writers, special instructions, accessibility needs.
- **FR-2.3**: Volunteers browse a prioritized feed with geolocation, filters, and action buttons (Commit, Backup, Message).
- **FR-2.4**: Automatic backup promotion when a primary volunteer cancels.

### 4.3 Verification & Attendance
- **FR-3.1**: Volunteers present physical Aadhaar at exam center; college verifies against uploaded copy.
- **FR-3.2**: Colleges mark attendance (Present/Absent) and verification outcome.
- **FR-3.3**: All verification and attendance logs are tamper-evident and exportable.

### 4.4 ComplaintBox & Moderation
- **FR-4.1**: Any role may submit complaints referencing public IDs (`student_id`, `volunteer_id`, `college_id`).
- **FR-4.2**: Admin triages complaints, suspends/flags accounts, and records outcomes in audit logs.

### 4.5 Help Desk
- **FR-5.1**: Real-time volunteer-staffed chat via WebSockets.
- **FR-5.2**: Volunteers operate in shifts/rotas.
- **FR-5.3**: Unresolved issues escalate to admin via ComplaintBox integration.

### 4.6 Dashboards
- **FR-6.1**: Role-specific dashboards summarizing active requests, commitments, verification queues, and complaints.
- **FR-6.2**: Admin dashboard with platform overview, audit log viewer, and moderation tools.

### 4.7 Trust & Reputation
- **FR-7.1**: Post-exam ratings (1–5) and feedback per engagement.
- **FR-7.2**: Trust signals surface reliable volunteers and flag repeat issues.

### 4.8 Account Lifecycle
- **FR-8.1**: Users may request logical deletion (deactivation).
- **FR-8.2**: Deactivated accounts hide profiles and prevent new actions but preserve historical logs and audit trails.
- **FR-8.3**: Reactivation only via admin.

## 5. Non-Functional Requirements
- **NFR-1 Accessibility**: WCAG 2.1 AA; ARIA roles; keyboard-only navigation; screen reader optimized.
- **NFR-2 Security**: Encrypted Aadhaar storage at rest; role-based access control; admin MFA; JWT auth.
- **NFR-3 Compliance**: Aadhaar handling and data retention reviewed by legal counsel; local data-protection compliance.
- **NFR-4 Performance**: Page load <2s; chat latency <300ms; feed refresh <1s.
- **NFR-5 Reliability**: 99.5% uptime during exam seasons; automated backups.
- **NFR-6 Scalability**: Support 500 concurrent users and 10,000 requests/semester in MVP.

## 6. Release Phases
| Phase | Deliverables | Timeline |
|-------|-------------|----------|
| **MVP** | Auth, request posting, commit/backup, verification logging, basic dashboards | Month 1–2 |
| **Pilot** | Help desk chat, ComplaintBox, audit exports, accessibility audit | Month 3 |
| **Launch** | Public repo, community governance, legal compliance sign-off | Month 4 |
| **Scale** | Mobile responsiveness, regional language support, analytics | Month 5–6 |
