-- ============================================================================
-- BloodLink: Test and Verification Queries (Panvel Region)
-- Use in pgAdmin 4 or VS Code SQL Console to test your schema & functionality
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SELECT STATEMENTS FOR TESTING
-- ----------------------------------------------------------------------------

-- A. View all registered delivery partners in Panvel with their GPS coordinates
SELECT id, partner_name, phone, vehicle_type, location, availability_status, current_latitude, current_longitude 
FROM delivery_partners 
ORDER BY id ASC;

-- B. Retrieve only partners available for instant blood delivery assignment
SELECT id, partner_name, phone, vehicle_type, location, current_latitude, current_longitude 
FROM delivery_partners 
WHERE availability_status = 'Available'
ORDER BY id ASC;

-- C. Check deliveries table (should be 0 records initially until Flask backend inserts)
SELECT * FROM deliveries;

-- D. Check location breadcrumb logs (should be empty initially)
SELECT * FROM location_updates;

-- E. Summary count of delivery partners grouped by availability status
SELECT availability_status, COUNT(*) AS total_partners 
FROM delivery_partners 
GROUP BY availability_status;


-- ----------------------------------------------------------------------------
-- 2. UPDATE STATEMENTS FOR TESTING RIDER GPS MOVEMENT & STATUS IN PANVEL
-- ----------------------------------------------------------------------------

-- A. Simulate rider #1 (Rahul Sharma) moving from Shivaji Chowk towards Panvel Railway Station
UPDATE delivery_partners
SET 
    current_latitude = 18.990200,
    current_longitude = 73.120700
WHERE id = 1;

-- B. Change rider #1 status to 'Busy' when assigned to an emergency delivery
UPDATE delivery_partners
SET availability_status = 'Busy'
WHERE id = 1;

-- C. Set rider back to 'Available' once delivered
UPDATE delivery_partners
SET availability_status = 'Available'
WHERE id = 1;


-- ----------------------------------------------------------------------------
-- 3. INTEGRATION TEST: SIMULATE A FULL DELIVERY & GPS TRACKING FLOW IN PANVEL
-- (Simulates blood dispatched from MGM Hospital Kamothe to SDH Old Panvel)
-- ----------------------------------------------------------------------------

-- Step I: Flask backend inserts a new delivery request (assigned to partner #5 near Kamothe)
INSERT INTO deliveries (
    partner_id, customer_name, customer_phone, blood_group, 
    hospital_name, destination, destination_latitude, destination_longitude, 
    status, eta_minutes
) VALUES (
    5, 'Rohan Deshmukh', '+919123456789', 'O+', 
    'MGM Hospital & Blood Bank, Kamothe', 'Sub-District Hospital (SDH), Old Panvel', 
    18.992500, 73.118000, 'Assigned', 18
);

-- Step II: Rider accepts and starts moving on the Sion-Panvel Highway ('On the way')
UPDATE deliveries 
SET status = 'On the way', eta_minutes = 12, updated_at = CURRENT_TIMESTAMP 
WHERE id = 1;

-- Step III: Rider app sends GPS breadcrumbs along the Sion-Panvel Highway into location_updates
INSERT INTO location_updates (delivery_id, partner_id, latitude, longitude)
VALUES 
    (1, 5, 19.020500, 73.093500),  -- Near MGM Hospital, Kamothe
    (1, 5, 19.008500, 73.105000),  -- Khanda Colony flyover
    (1, 5, 18.995000, 73.115000);  -- Approaching Old Panvel

-- Step IV: Frontend queries the latest live GPS coordinate for delivery #1
SELECT 
    d.id AS delivery_id,
    d.status,
    d.eta_minutes,
    d.hospital_name,
    d.destination,
    p.partner_name,
    p.phone AS partner_phone,
    lu.latitude AS live_latitude,
    lu.longitude AS live_longitude,
    lu.recorded_at AS last_ping_time
FROM deliveries d
JOIN delivery_partners p ON d.partner_id = p.id
JOIN location_updates lu ON lu.delivery_id = d.id
WHERE d.id = 1
ORDER BY lu.recorded_at DESC
LIMIT 1;

-- Step V: Clean up test delivery so database stays fresh for the Flask backend
DELETE FROM deliveries WHERE id = 1;
