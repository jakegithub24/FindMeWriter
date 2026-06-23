# RULES.md — Development Rules & Coding Standards

## 1. Git Workflow
- **Branching**: `main` is production-ready. Use feature branches: `feature/S{ID}-short-name`.
- **Commits**: Use conventional commits:
  - `feat:` new feature
  - `fix:` bug fix
  - `docs:` documentation
  - `test:` tests
  - `refactor:` code restructuring
  - `security:` security-related changes
- **Pull Requests**: Require 1 review for non-admin changes; 2 reviews for auth/security changes.
- **Merges**: Squash and merge to `main` to maintain clean history.

## 2. Python Code Style
- Follow **PEP 8** strictly.
- Use **Black** formatter (`line-length 88`) and **isort** for imports.
- Type hints on all function signatures (`def create_user(data: dict) -> User:`).
- Docstrings for every module, class, and public function (Google style).
- No bare `except:` — always catch specific exceptions.
- No `print()` — use logging (`app.logger` or `structlog`).

## 3. Database Rules
- **Never** concatenate SQL. Use parameterized queries exclusively.
- Every mutating operation must be wrapped in a transaction.
- Foreign keys must have `ON DELETE`/`ON UPDATE` rules defined.
- Add indexes for any column used in `WHERE`, `JOIN`, or `ORDER BY`.
- Schema changes require migration scripts (even for SQLite, use numbered `.sql` files).

## 4. Security Rules
- All passwords: bcrypt with cost ≥ 12.
- JWT secret: 32+ byte random string from environment.
- Aadhaar files: encrypt with Fernet before saving; serve only through authenticated view functions.
- Admin routes: require both valid JWT **and** TOTP verification.
- Rate limit auth endpoints: 5 attempts per 15 minutes.
- Sanitize all user inputs; rely on Jinja2 auto-escaping for XSS prevention.
- Set security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`.

## 5. Accessibility Rules
- Every page must pass axe-core automated tests.
- All forms use `<label>` elements with `for` attributes.
- All images must have `alt` text (empty `alt=""` only for decorative).
- Focus order must be logical; never remove focus indicators.
- Color contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text.
- Interactive elements must be reachable via keyboard (Tab, Enter, Space, Escape).

## 6. Testing Requirements
- **Unit Tests**: pytest for all utility functions and middleware.
- **Integration Tests**: Test client for all API endpoints.
- **Accessibility Tests**: pytest-playwright or axe-core CLI for critical user flows.
- **Coverage**: Minimum 80% for `middleware/`, `models/`, `utils/`.
- **Security Tests**: Dependency scanning (`safety`, `bandit`) in CI.

## 7. Audit & Logging Rules
- Every `POST`, `PUT`, `DELETE`, and `PATCH` must trigger an audit log entry via decorator.
- Audit logs are **append-only**. No UPDATE or DELETE on `audit_logs` table.
- Include actor, action, target, timestamp, and serialized context in every entry.
- Hash chain: each entry includes SHA-256 of `(previous_hash + current_data)`.

## 8. Frontend Rules
- All templates extend `base.html`.
- Use Bootstrap grid classes; avoid custom CSS for layout where possible.
- JavaScript modules in `static/js/`; no inline `<script>` blocks in templates.
- Theme preference read before render to prevent flash of unstyled content.
- All AJAX requests include `X-CSRF-Token` header where applicable.

## 9. Documentation Rules
- Update `README.md` if setup steps change.
- Document all environment variables in `.env.example`.
- API changes require updating inline docstrings and user-facing docs.
- Complex business logic must include a comment referencing the relevant PRD/TRD section.

## 10. Review Checklist (For PRs)
- [ ] Code follows style guide (Black, isort)
- [ ] Tests added and passing
- [ ] Security: no secrets, no SQL injection vectors
- [ ] Accessibility: labels, ARIA, focus order checked
- [ ] Audit logging added for mutating changes
- [ ] Documentation updated
- [ ] PR description links to related issue/task ID
