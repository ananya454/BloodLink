# BloodLink - Delivery & Real-Time Tracking Database Module (Panvel Region)

**Role: Person 1 (Database Developer)**  
Tech Stack: PostgreSQL 12+, Python 3, `psycopg2-binary`

---

## 📁 Project Structure

```text
BloodLink/
├── database/
│   ├── delivery_schema.sql    # Tables (delivery_partners, deliveries, location_updates) + Indexes
│   ├── seed_partners.sql      # Realistic delivery riders in Panvel with GPS coordinates
│   └── test_queries.sql       # SELECT, UPDATE & live tracking simulation SQL for Panvel
├── setup_delivery_db.py       # Initializes tables and seeds partners via Python
├── test_delivery_db.py        # Runs full test suite & simulated GPS movement test in Panvel
├── .env                       # Local PostgreSQL connection settings
├── .env.example               # Template for DB credentials
├── .gitignore                 # Ignores sensitive and virtualenv files
└── README.md                  # Complete documentation and team integration specs
```

---

## 📍 Seeded Delivery Partners (Panvel & Navi Mumbai Nodes)

| ID | Partner Name | Vehicle | Panvel Location | Lat, Long | Status |
|---|---|---|---|---|---|
| 1 | Rahul Sharma | Motorcycle (Bajaj Pulsar 150) | Old Panvel (Near Shivaji Chowk) | `18.989400, 73.112100` | Available |
| 2 | Priya Patel | Electric Scooter (Ather 450X) | New Panvel (Sector 19) | `18.998400, 73.125600` | Available |
| 3 | Arun Kumar | Scooter (Honda Activa 6G) | Khanda Colony, New Panvel | `19.006200, 73.109800` | Busy |
| 4 | Sneha Varma | Motorcycle (Hero Splendor) | Kalamboli (Near Highway Circle) | `19.027000, 73.102500` | Offline |
| 5 | Mohammed Faiz | Electric Bike (Revolt RV400) | Kamothe (Near MGM Hospital) | `19.020500, 73.093500` | Available |
| 6 | Vikram Singh | Motorcycle (TVS Apache 160) | Karanjade (Sector 4) | `18.975000, 73.098000` | Available |

---

## 🚀 How to Run Directly in VS Code

### 1. Open this folder in VS Code
In VS Code, go to **File** $\rightarrow$ **Open Folder...** and select:
```text
/Users/ananya/.gemini/antigravity/scratch/BloodLink
```

### 2. Configure Database Password
Open the `.env` file in VS Code and set your PostgreSQL password (the password you use in pgAdmin):
```env
DB_NAME=bloodlink_db
DB_USER=postgres
DB_PASSWORD=your_actual_password_here
DB_HOST=localhost
DB_PORT=5432
```
*(Make sure the database `bloodlink_db` exists in pgAdmin. If not, right-click "Databases" in pgAdmin and click "Create Database")*

### 3. Install Python Dependencies
Open the VS Code Terminal (`Ctrl + \`` or `Cmd + \``) and run:
```bash
pip install psycopg2-binary python-dotenv
```

### 4. Create Tables & Seed Data
In the VS Code terminal, run:
```bash
python setup_delivery_db.py
```
This runs `delivery_schema.sql` and `seed_partners.sql` automatically.

### 5. Run Verification & Panvel GPS Tracking Test
In the VS Code terminal, run:
```bash
python test_delivery_db.py
```
This tests:
- Available delivery partners in Panvel.
- Confirms 0 fake deliveries exist.
- Checks foreign keys between tables.
- Runs a live GPS simulation along the Sion-Panvel Highway route (MGM Hospital Kamothe $\rightarrow$ SDH Old Panvel) and cleans up.

---

## 🛠️ Alternative: Running in pgAdmin 4

If you prefer running SQL directly in pgAdmin:
1. Open **pgAdmin 4** $\rightarrow$ Right-click your database (`bloodlink_db`) $\rightarrow$ Click **Query Tool**.
2. Open and run `database/delivery_schema.sql` (Press `F5`).
3. Open and run `database/seed_partners.sql` (Press `F5`).
4. To test queries, open `database/test_queries.sql` and run individual statements.

---

## 🤝 Integration Hand-off

### For Person 2 (Flask Backend / API Developer)

#### 1. Assigning an Available Panvel Partner to a Blood Request
```sql
SELECT id, partner_name, phone, vehicle_type, location, current_latitude, current_longitude
FROM delivery_partners
WHERE availability_status = 'Available'
ORDER BY id ASC;
```

#### 2. Creating a Delivery Record
```sql
INSERT INTO deliveries (
    partner_id, customer_name, customer_phone, blood_group,
    hospital_name, destination, destination_latitude, destination_longitude,
    status, eta_minutes
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, 'Assigned', %s
) RETURNING id;
```

#### 3. Ingesting Rider GPS Updates (`POST /api/rider/location`)
When the rider moves, update `delivery_partners` and add a trail to `location_updates`:
```sql
-- Update current location
UPDATE delivery_partners
SET current_latitude = %s, current_longitude = %s
WHERE id = %s;

-- Append to location updates history
INSERT INTO location_updates (delivery_id, partner_id, latitude, longitude)
VALUES (%s, %s, %s, %s);
```

#### 4. Querying Delivery with Latest Rider GPS (For Tracking API)
```sql
SELECT 
    d.id AS delivery_id,
    d.status,
    d.eta_minutes,
    d.hospital_name,
    d.destination,
    d.destination_latitude,
    d.destination_longitude,
    p.partner_name,
    p.phone AS partner_phone,
    p.vehicle_type,
    p.location AS partner_base_location,
    p.current_latitude AS rider_latitude,
    p.current_longitude AS rider_longitude
FROM deliveries d
LEFT JOIN delivery_partners p ON d.partner_id = p.id
WHERE d.id = %s;
```

---

### For Person 3 (Frontend / Map & Tracking Developer)

When Person 3 calls `GET /api/deliveries/<id>/track`, the Flask API returns:

```json
{
  "delivery_id": 1,
  "status": "On the way",
  "eta_minutes": 12,
  "blood_group": "B+",
  "hospital_name": "MGM Hospital & Blood Bank, Kamothe",
  "destination": "Sub-District Hospital (SDH), Old Panvel",
  "destination_coordinates": {
    "latitude": 18.992500,
    "longitude": 73.118000
  },
  "partner": {
    "name": "Rahul Sharma",
    "phone": "+919876543210",
    "vehicle_type": "Motorcycle (Bajaj Pulsar 150)",
    "current_coordinates": {
      "latitude": 18.990200,
      "longitude": 73.120700
    }
  }
}
```

* **Map Destination Marker:** Pin at `destination_coordinates` (SDH Old Panvel).
* **Rider Moving Marker:** Pin at `partner.current_coordinates` (Near Panvel Railway Station).
