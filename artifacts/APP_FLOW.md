# APP_Flow.md — Application & User Flow

## 1. System Context
```
[Student] ←→ [FindMeWriter Platform] ←→ [Volunteer]
                ↕
[College] ←→ [Admin]
```

## 2. Student Flow

```
[Start]
  │
  ▼
[Register] ──► Upload Aadhaar + Enter Number ──► [Receive student_id]
  │
  ▼
[Complete Profile] ──► Accessibility Preferences
  │
  ▼
[Create Request] ──► Date/Time/Location/Language/Duration/Writers/Special Needs
  │
  ▼
[Track Request] ──► View Committed Volunteer ──► Message Volunteer
  │
  ▼
[Exam Day] ──► Volunteer Arrives ──► Post-Exam Rating & Feedback
  │
  ▼
[Optional: File Complaint] ──► Reference public IDs ──► Track Resolution
  │
  ▼
[Request Account Deletion] ──► Confirm ──► Logical Deactivate
```

## 3. Volunteer Flow

```
[Start]
  │
  ▼
[Register] ──► Upload Aadhaar + Enter Number ──► [Receive volunteer_id]
  │
  ▼
[Browse Feed] ──► Filter by City/Language/Date ──► View Request Cards
  │
  ▼
[Commit] ──► Primary OR Backup ──► Confirmation
  │
  ▼
[Receive Reminder] ──► Attend Exam with Physical Aadhaar
  │
  ▼
[College Verifies] ──► Attendance Marked
  │
  ▼
[Receive Rating] ──► Trust Score Updated
  │
  ▼
[Optional: Sign Up for Help Desk Shift]
```

## 4. College Flow

```
[Start]
  │
  ▼
[Create Institutional Profile] ──► Coordinate with Admin for Verification
  │
  ▼
[Post Request] ──► Single or Bulk Writers Needed
  │
  ▼
[Verification Queue] ──► Volunteer Arrives ──► Compare Physical Aadhaar vs Uploaded Copy
  │                                              │
  │◄──── Match? ──► Yes: Log Verified          No: Log Mismatch + Notes
  │
  ▼
[Mark Attendance] ──► Present / Absent per Volunteer
  │
  ▼
[Export Logs] ──► CSV/JSON for Audit
  │
  ▼
[Handle Complaints] ──► Review Incoming ──► Respond/Escalate
```

## 5. Admin Flow

```
[Login + TOTP MFA]
  │
  ▼
[Dashboard Overview] ──► User Counts │ Pending Complaints │ Recent Activity
  │
  ├──► [User Management] ──► Suspend/Flag/Reactivate Accounts
  │
  ├──► [Audit Logs] ──► Filter by Action/Actor/Date ──► Verify Hash Chain
  │
  ├──► [Complaint Triage] ──► Review Evidence ──► Record Outcome
  │
  ├──► [Exports] ──► Generate CSV/JSON ──► Download
  │
  └──► [Help Desk Oversight] ──► Monitor Chat Rooms ──► Handle Escalations
```

## 6. Help Desk Flow

```
[User Opens Chat]
  │
  ▼
[Socket Connection] ──► Join Room
  │
  ▼
[Volunteer Online?] ──► Yes: Real-time Chat
  │                       No: Leave Message + Auto-Escalation Option
  │
  ▼
[Issue Resolved?] ──► Yes: Close Chat ──► Log Interaction
  │                     No: Escalate to Admin ──► Create Complaint Ticket
  │
  ▼
[Audit Log Entry]
```

## 7. ComplaintBox Flow

```
[Submit Complaint]
  │
  ▼
[Select Target Role] ──► Enter Target public_id
  │
  ▼
[Describe Issue] ──► Attach Files (optional)
  │
  ▼
[Admin Review Queue] ──► Status: Open
  │
  ▼
[Admin Investigates] ──► Access Audit Logs ──► Interview Parties
  │
  ▼
[Resolution] ──► Status: Resolved │ Action: Suspend/Flag/No Action
  │
  ▼
[Outcome Logged to Audit Trail]
```

## 8. State Diagram: Request Lifecycle

```
[OPEN] ──► Volunteer Commits ──► [FILLED]
  │                                    │
  │◄── Backup Cancels ──► [OPEN]      │
  │                                    │
  │◄── Primary Cancels ──► Auto-Promote Backup ──► [FILLED]
  │                                    │
  │                                    ▼
  │                              [Exam Completed]
  │                                    │
  │                                    ▼
  │                              [CLOSED]
  │                                    │
  ▼                                    ▼
[CANCELLED] ◄────────────────── Any Role Cancels (before exam)
```
