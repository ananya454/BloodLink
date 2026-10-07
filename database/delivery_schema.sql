-- ============================================================================
-- BloodLink: Delivery & Real-Time Tracking Schema
-- Role: Person 1 (Database Developer)
-- Compatible with PostgreSQL 12+ / pgAdmin 4 / VS Code PostgreSQL Extension
-- ============================================================================

-- 1. Table: delivery_partners
-- Stores rider profile, vehicle information, status, and current GPS coordinates.
CREATE TABLE IF NOT EXISTS delivery_partners (
    id SERIAL PRIMARY KEY,
    partner_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    vehicle_type VARCHAR(50) NOT NULL,
    location VARCHAR(150) NOT NULL,
    availability_status VARCHAR(20) DEFAULT 'Offline' NOT NULL
        CHECK (availability_status IN ('Available', 'Busy', 'Offline')),
    current_latitude NUMERIC(10, 6),
    current_longitude NUMERIC(10, 6)
);

-- 2. Table: deliveries
-- Stores active and historical blood delivery requests.
CREATE TABLE IF NOT EXISTS deliveries (
    id SERIAL PRIMARY KEY,
    partner_id INT REFERENCES delivery_partners(id) ON DELETE SET NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(15) NOT NULL,
    blood_group VARCHAR(10) NOT NULL,
    hospital_name VARCHAR(150) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    destination_latitude NUMERIC(10, 6),
    destination_longitude NUMERIC(10, 6),
    status VARCHAR(20) DEFAULT 'Assigned' NOT NULL
        CHECK (status IN ('Assigned', 'On the way', 'Arrived', 'Completed', 'Cancelled')),
    eta_minutes INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Table: location_updates
-- Stores historical GPS breadcrumb tracking points for moving riders over time.
CREATE TABLE IF NOT EXISTS location_updates (
    id SERIAL PRIMARY KEY,
    delivery_id INT NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,
    partner_id INT NOT NULL REFERENCES delivery_partners(id) ON DELETE CASCADE,
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(10, 6) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Fast Query Performance
-- ============================================================================

-- Faster lookup when assigning free riders
CREATE INDEX IF NOT EXISTS idx_partners_availability 
    ON delivery_partners(availability_status);

-- Faster lookup for active deliveries by partner and status
CREATE INDEX IF NOT EXISTS idx_deliveries_partner_id 
    ON deliveries(partner_id);

CREATE INDEX IF NOT EXISTS idx_deliveries_status 
    ON deliveries(status);

-- Fast lookup for real-time tracking route history and latest rider GPS ping
CREATE INDEX IF NOT EXISTS idx_location_updates_delivery_time 
    ON location_updates(delivery_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_location_updates_partner_id 
    ON location_updates(partner_id);
