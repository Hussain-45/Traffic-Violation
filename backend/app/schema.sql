-- SQL Schema DDL for Smart Traffic Violation Detection System
-- Database: PostgreSQL

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'officer', -- admin, officer
    status VARCHAR(50) DEFAULT 'active', -- active, inactive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);


-- 2. Locations Table
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    risk_level VARCHAR(50) DEFAULT 'low', -- low, medium, high
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name);


-- 3. Cameras Table
CREATE TABLE IF NOT EXISTS cameras (
    id VARCHAR(255) PRIMARY KEY, -- e.g., CAM-001
    name VARCHAR(255) NOT NULL,
    location_id INT REFERENCES locations(id) ON DELETE SET NULL,
    location VARCHAR(255) NOT NULL,
    ip_address VARCHAR(255),
    status VARCHAR(50) DEFAULT 'online', -- online, offline
    health_status VARCHAR(50) DEFAULT 'good', -- good, warning, critical
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cameras_status ON cameras(status);


-- 4. Vehicles Table
CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    license_plate VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL, -- car, motorcycle, truck, bus, auto
    brand VARCHAR(255),
    color VARCHAR(100),
    owner_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'valid', -- valid, expired, stolen, suspended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vehicles_plate ON vehicles(license_plate);


-- 5. Violations Table
CREATE TABLE IF NOT EXISTS violations (
    id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES vehicles(id) ON DELETE CASCADE NOT NULL,
    camera_id VARCHAR(255) REFERENCES cameras(id) ON DELETE CASCADE NOT NULL,
    type VARCHAR(100) NOT NULL, -- red_light_jump, wrong_lane, overspeeding, etc.
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(255) NOT NULL,
    fine_amount DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, paid, resolved
    evidence_image_path VARCHAR(255),
    evidence_video_path VARCHAR(255),
    confidence_score DOUBLE PRECISION DEFAULT 1.0,
    officer_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_violations_type ON violations(type);
CREATE INDEX IF NOT EXISTS idx_violations_status ON violations(status);


-- 6. Fine Rules Table
CREATE TABLE IF NOT EXISTS fine_rules (
    id SERIAL PRIMARY KEY,
    violation_type VARCHAR(100) UNIQUE NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_fine_rules_type ON fine_rules(violation_type);


-- 7. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    violation_id INT REFERENCES violations(id) ON DELETE CASCADE NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    payment_method VARCHAR(100) NOT NULL, -- credit_card, debit_card, upi, cash
    status VARCHAR(50) DEFAULT 'completed' -- completed, failed, pending
);

CREATE INDEX IF NOT EXISTS idx_payments_txn ON payments(transaction_id);


-- 8. Reports Table
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    generated_by INT REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    report_type VARCHAR(100) NOT NULL, -- violations, revenue, analytics
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 9. Settings Table
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);


-- 10. Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    action TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
