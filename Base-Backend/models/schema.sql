-- SQLite schema for FindMeWriter

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL CHECK(role IN ('student','volunteer','college','admin')),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active','deactivated')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    user_id INTEGER PRIMARY KEY,
    student_id TEXT UNIQUE NOT NULL,
    aadhaar_number_hash TEXT NOT NULL,
    aadhaar_copy_path TEXT NOT NULL,
    institution TEXT,
    accessibility_needs TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS volunteers (
    user_id INTEGER PRIMARY KEY,
    volunteer_id TEXT UNIQUE NOT NULL,
    aadhaar_number_hash TEXT NOT NULL,
    aadhaar_copy_path TEXT NOT NULL,
    city TEXT,
    languages TEXT,
    rating_avg REAL DEFAULT 0.0,
    total_exams INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS colleges (
    user_id INTEGER PRIMARY KEY,
    college_id TEXT UNIQUE NOT NULL,
    institution_name TEXT NOT NULL,
    affiliation_code TEXT,
    address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_by INTEGER NOT NULL,
    creator_role TEXT NOT NULL CHECK(creator_role IN ('student','college')),
    date DATE NOT NULL,
    time TIME NOT NULL,
    location TEXT NOT NULL,
    language TEXT NOT NULL,
    duration INTEGER NOT NULL,
    num_writers INTEGER DEFAULT 1,
    special_needs TEXT,
    status TEXT DEFAULT 'open' CHECK(status IN ('open','filled','completed','cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS commitments (
    commitment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    volunteer_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('primary','backup')),
    status TEXT DEFAULT 'active' CHECK(status IN ('active','cancelled','fulfilled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests(request_id) ON DELETE CASCADE,
    FOREIGN KEY (volunteer_id) REFERENCES volunteers(user_id)
);

CREATE TABLE IF NOT EXISTS verifications (
    verification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    volunteer_id INTEGER NOT NULL,
    college_id INTEGER NOT NULL,
    verified_by_user_id INTEGER NOT NULL,
    physical_match BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (request_id) REFERENCES requests(request_id),
    FOREIGN KEY (volunteer_id) REFERENCES volunteers(user_id),
    FOREIGN KEY (college_id) REFERENCES colleges(user_id),
    FOREIGN KEY (verified_by_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    complainant_id INTEGER NOT NULL,
    target_id TEXT NOT NULL,
    target_role TEXT NOT NULL,
    description TEXT NOT NULL,
    attachments_json TEXT DEFAULT '[]',
    status TEXT DEFAULT 'open' CHECK(status IN ('open','under_review','resolved')),
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (complainant_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    actor_id INTEGER,
    actor_role TEXT NOT NULL,
    target_id INTEGER,
    details_json TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ratings (
    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,
    score INTEGER CHECK(score >= 1 AND score <= 5),
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests(request_id),
    FOREIGN KEY (from_id) REFERENCES users(id),
    FOREIGN KEY (to_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS helpdesk_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    sender_id INTEGER NOT NULL,
    sender_role TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_date ON requests(date);
CREATE INDEX IF NOT EXISTS idx_commitments_volunteer ON commitments(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_commitments_request ON commitments(request_id);
CREATE INDEX IF NOT EXISTS idx_verifications_request ON verifications(request_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_helpdesk_room ON helpdesk_messages(room_id);

