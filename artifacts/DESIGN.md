# DESIGN.md — Design System & UI/UX Specification

## 1. Design Philosophy
**Accessibility-First, Dignity-Always.** Every interface must be usable by a screen-reader-dependent user operating with keyboard-only navigation. Visual design supports, never replaces, semantic structure.

## 2. Color Palette

### Base Theme
| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary` | `#0056b3` | Primary actions, links |
| `--color-primary-hover` | `#003d80` | Hover states |
| `--color-success` | `#2e7d32` | Success, verified, present |
| `--color-warning` | `#ed6c02` | Backup, pending |
| `--color-danger` | `#d32f2f` | Error, absent, complaint |
| `--color-surface` | `#ffffff` | Card backgrounds |
| `--color-background` | `#f5f5f5` | Page background |
| `--color-text` | `#212121` | Primary text |
| `--color-text-muted` | `#616161` | Secondary text |

### High-Contrast Theme
| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary` | `#005a9c` | Actions |
| `--color-text` | `#000000` | Text |
| `--color-background` | `#ffffff` | Background |
| `--color-border` | `#000000` | All borders 2px solid |

### Large-Text Theme
- Base font size: `18px` (vs standard `16px`)
- Line height: `1.6`
- Minimum touch target: `48px × 48px`

## 3. Typography
- **Primary**: `Inter` (Google Fonts) — clean, legible UI text
- **Accessibility**: `Atkinson Hyperlegible` (Google Fonts) — optimized for low vision; used in high-contrast theme
- **Scale**:
  - H1: `2rem` (32px), weight 700
  - H2: `1.5rem` (24px), weight 600
  - Body: `1rem` (16px), weight 400, line-height 1.5
  - Small: `0.875rem` (14px), weight 400

## 4. Layout Grid
- Bootstrap 5 grid system: `container` → `row` → `col-*`
- Max content width: `1140px`
- Gutters: `24px`
- Mobile-first breakpoints: `sm(576)`, `md(768)`, `lg(992)`, `xl(1200)`

## 5. Component Specifications

### Navigation
- **Skip Link**: First focusable element on every page: `<a href="#main-content" class="visually-hidden-focusable">Skip to main content</a>`
- **Navbar**: Bootstrap `navbar-expand-lg`, sticky top, `aria-label="Main navigation"`
- **Role Badge**: Displayed next to username with distinct color coding

### Forms
- Every input has an associated `<label>` (never placeholder-only).
- `aria-describedby` links to help text and error messages.
- Error messages use `role="alert"` and `aria-live="polite"`.
- File upload: explicit `accept` attribute, file size warning, `aria-label="Upload Aadhaar photocopy"`

### Cards (Request Feed)
- Container: `div` with `role="article"` and `aria-labelledby="request-title-{{id}}"`
- Structure: Title, metadata list (date, location, language), action button group
- Focus order: Title → Details → Actions

### Tables (Audit Logs, Verification Queue)
- `<table>` with `<caption>` describing contents.
- Column headers use `scope="col"`.
- Sortable columns indicated with `aria-sort`.

### Modals
- `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to modal title.
- Focus trap: Tab cycles within modal; ESC closes.
- Return focus to trigger element on close.

### Chat Interface
- Message container: `aria-live="polite"`, `aria-relevant="additions"`
- Incoming messages: `aria-label="Message from [Name] at [Time]"`
- Typing indicator: `aria-live="polite"` status region

## 6. Accessibility Checklist (Per Page)
- [ ] Skip-to-content link visible on focus
- [ ] Logical heading hierarchy (`h1` → `h2` → `h3`)
- [ ] All images have descriptive `alt` text (or `alt=""` if decorative)
- [ ] Focus indicators: `outline: 3px solid #0056b3; outline-offset: 2px`
- [ ] Color is never the sole indicator of status (icons + text)
- [ ] Form errors associated with inputs via `aria-describedby`
- [ ] Keyboard operable: no mouse-only interactions
- [ ] Screen reader tested with NVDA/VoiceOver

## 7. Theme Implementation
- CSS variables in `:root` for base; override in `[data-theme="high-contrast"]` and `[data-theme="large-text"]`.
- Theme preference stored in `localStorage`; applied before render to prevent flash.
- Toggle button: `aria-pressed="true/false"`, accessible via keyboard.
