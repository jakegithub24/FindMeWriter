# IMPLEMENTATION.md — Implementation Plan & Roadmap

## 1. Philosophy
Build the MVP as a **vertical slice**: one complete user journey (Student registers → posts request → Volunteer commits → College verifies → Rating submitted) before expanding breadth. This validates core architecture and accessibility assumptions early.

## 2. Phase Breakdown

### Phase 0: Foundation (Week 1)
- [x] Set up Flask app factory, config classes, and SQLite connection
- [x] Implement base Jinja2 template with Bootstrap 5, theme toggle, skip links
- [x] Write `schema.sql` and `db.py` with initialization CLI
- [x] Set up GitHub Actions CI (lint, basic test runner)


### Phase 1: Authentication & Identity (Week 2)
- [x] Role-based registration with file upload (Aadhaar encryption)
- [x] Login/logout with JWT (access + refresh)
- [x] Profile completion pages per role
- [x] Public ID generation utility
- [x] Admin MFA with TOTP
- [x] **Milestone**: All four roles can register and log in securely

### Phase 2: Request & Matching (Week 3)
- [ ] Student request creation form
- [ ] College bulk request posting
- [ ] Volunteer feed with filters (location, language, date)
- [ ] Commit/backup flow with database transactions
- [ ] Automatic backup promotion on cancellation
- [ ] Dashboards for Student, Volunteer, College
- [ ] **Milestone**: End-to-end request matching works

### Phase 3: Verification & Audit (Week 4)
- [ ] College verification queue UI (side-by-side Aadhaar comparison)
- [ ] Verification logging endpoint
- [ ] Attendance marking (Present/Absent)
- [ ] Audit log decorator and hash chain implementation
- [ ] Admin audit log viewer with filtering
- [ ] **Milestone**: Verification and attendance are tamper-evident

### Phase 4: ComplaintBox & Moderation (Week 5)
- [ ] Complaint submission with target ID validation
- [ ] Admin complaint triage queue
- [ ] Account suspension/flagging
- [ ] Outcome logging to audit trail
- [ ] **Milestone**: Complaint resolution cycle complete

### Phase 5: Real-time Help Desk (Week 6)
- [ ] Flask-SocketIO integration
- [ ] Chat room UI with volunteer online status
- [ ] Message persistence
- [ ] Escalation to admin
- [ ] Volunteer shift rota signup
- [ ] **Milestone**: Real-time support functional

### Phase 6: Trust, Ratings & UX Polish (Week 7)
- [ ] Post-exam rating form (1–5 stars, accessible)
- [ ] Trust signals on volunteer profiles
- [ ] Account deletion (logical) flow
- [ ] Admin export tools (CSV/JSON)
- [ ] High-contrast and large-text theme refinement
- [ ] **Milestone**: Platform feature-complete for pilot

### Phase 7: Pilot & Accessibility Audit (Week 8)
- [ ] Deploy to staging environment
- [ ] Recruit 2–3 colleges and 10–20 volunteers for pilot
- [ ] Conduct WCAG 2.1 AA audit with screen reader users
- [ ] Fix accessibility blockers
- [ ] Load test with 100 concurrent users
- [ ] **Milestone**: Pilot ready

### Phase 8: Launch & Community (Week 9–10)
- [ ] Legal review of Aadhaar handling and data retention
- [ ] Production deployment
- [ ] Publish documentation and API reference
- [ ] Onboard community moderators and help desk volunteers
- [ ] Announcement and user onboarding sessions
- [ ] **Milestone**: Public launch

## 3. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Aadhaar legal compliance issues | Medium | High | Early legal review; minimal data collection; encrypted storage |
| Accessibility gaps in pilot | Medium | High | Weekly screen-reader testing; involve visually impaired users in design |
| Low volunteer sign-up | Medium | Medium | Partner with NSS/NCC units; simplify onboarding to <5 min |
| SQLite concurrency limits | Low | Medium | Monitor write contention; migrate to PostgreSQL if scale demands |
| Security breach of identity docs | Low | Critical | Fernet encryption, strict RBAC, no direct file URLs, regular audits |

## 4. Definition of Done
- Code reviewed and merged to `main`
- Unit tests pass (>80% coverage on critical paths)
- Accessibility checklist completed for the feature
- Audit logging implemented for all mutating actions
- Documentation updated (inline comments + user guide)
