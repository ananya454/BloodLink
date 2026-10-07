-- ============================================================================
-- BloodLink: Seed Data for Delivery Partners (Panvel & Navi Mumbai Region)
-- Realistic delivery riders with vehicle types & initial GPS coordinates in Panvel
-- Note: Does NOT insert fake deliveries (Flask backend creates those dynamically)
-- ============================================================================

INSERT INTO delivery_partners 
    (partner_name, phone, vehicle_type, location, availability_status, current_latitude, current_longitude)
VALUES
    ('Rahul Sharma',   '+919876543210', 'Motorcycle (Bajaj Pulsar 150)', 'Old Panvel (Near Shivaji Chowk)',     'Available', 18.989400, 73.112100),
    ('Priya Patel',    '+919876543211', 'Electric Scooter (Ather 450X)', 'New Panvel (Sector 19)',              'Available', 18.998400, 73.125600),
    ('Arun Kumar',     '+919876543212', 'Scooter (Honda Activa 6G)',     'Khanda Colony, New Panvel',           'Busy',      19.006200, 73.109800),
    ('Sneha Varma',    '+919876543213', 'Motorcycle (Hero Splendor)',    'Kalamboli (Near Highway Circle)',      'Offline',   19.027000, 73.102500),
    ('Mohammed Faiz',  '+919876543214', 'Electric Bike (Revolt RV400)',  'Kamothe (Near MGM Hospital)',          'Available', 19.020500, 73.093500),
    ('Vikram Singh',   '+919876543215', 'Motorcycle (TVS Apache 160)',   'Karanjade (Sector 4)',                 'Available', 18.975000, 73.098000)
ON CONFLICT (phone) DO UPDATE 
SET 
    partner_name = EXCLUDED.partner_name,
    vehicle_type = EXCLUDED.vehicle_type,
    location = EXCLUDED.location,
    availability_status = EXCLUDED.availability_status,
    current_latitude = EXCLUDED.current_latitude,
    current_longitude = EXCLUDED.current_longitude;
