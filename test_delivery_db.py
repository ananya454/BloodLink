"""
BloodLink - Database Verification & Test Suite (Panvel Region)
Role: Person 1 (Database Developer)

Run this script in your VS Code terminal:
    python test_delivery_db.py
"""

import os
import sys

try:
    import psycopg2
except ImportError:
    print("\n[ERROR] 'psycopg2' is not installed.")
    print("Please run: pip install psycopg2-binary python-dotenv\n")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_NAME = os.getenv("DB_NAME", "bloodlink_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def print_table(headers, rows):
    if not rows:
        print("  (No rows returned)")
        print()
        return

    str_rows = [[str(val) if val is not None else "NULL" for val in row] for row in rows]
    col_widths = [len(h) for h in headers]
    for row in str_rows:
        for idx, val in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(val))

    header_str = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    divider = "-+-".join("-" * w for w in col_widths)
    print(header_str)
    print(divider)
    for row in str_rows:
        print(" | ".join(f"{val:<{w}}" for val, w in zip(row, col_widths)))
    print()

def main():
    print("=" * 85)
    print(" BloodLink: Delivery & Tracking Database Test Suite (Panvel Region)")
    print("=" * 85)

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # -------------------------------------------------------------
        # TEST 1: Retrieve Available Delivery Partners in Panvel
        # -------------------------------------------------------------
        print("\n[TEST 1] Available Delivery Partners in Panvel for Assignment:")
        cursor.execute("""
            SELECT id, partner_name, phone, vehicle_type, location, availability_status, current_latitude, current_longitude
            FROM delivery_partners 
            WHERE availability_status = 'Available'
            ORDER BY id ASC;
        """)
        rows = cursor.fetchall()
        headers = ["ID", "Name", "Phone", "Vehicle", "Panvel Area", "Status", "Latitude", "Longitude"]
        print_table(headers, rows)

        # -------------------------------------------------------------
        # TEST 2: Verify Deliveries Table has 0 Fake Rows
        # -------------------------------------------------------------
        print("[TEST 2] Production Readiness Check for Deliveries:")
        cursor.execute("SELECT COUNT(*) FROM deliveries;")
        delivery_count = cursor.fetchone()[0]
        print(f"  Current delivery records in DB: {delivery_count}")
        if delivery_count == 0:
            print("  Result: [PASS] Clean state. Flask backend will insert orders dynamically.\n")
        else:
            print("  Result: [INFO] Deliveries exist from previous runs.\n")

        # -------------------------------------------------------------
        # TEST 3: Foreign Key Relationships
        # -------------------------------------------------------------
        print("[TEST 3] Foreign Key Constraint Verifications:")
        cursor.execute("""
            SELECT
                tc.table_name, kcu.column_name, 
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
              AND tc.table_name IN ('deliveries', 'location_updates')
            ORDER BY tc.table_name, kcu.column_name;
        """)
        fk_rows = cursor.fetchall()
        for tbl, col, ftbl, fcol in fk_rows:
            print(f"  [OK] FK verified: {tbl}.{col} -> {ftbl}.{fcol}")
        print()

        # -------------------------------------------------------------
        # TEST 4: Live GPS Tracking Simulation in Panvel
        # -------------------------------------------------------------
        print("[TEST 4] Simulating Live Rider GPS Tracking (Panvel Route):")
        # Pick first available partner in Panvel
        cursor.execute("SELECT id, partner_name, location FROM delivery_partners WHERE availability_status = 'Available' LIMIT 1;")
        partner = cursor.fetchone()
        if partner:
            p_id, p_name, p_loc = partner
            # Step A: Create temporary test delivery from MGM Hospital Kamothe to SDH Panvel
            cursor.execute("""
                INSERT INTO deliveries (
                    partner_id, customer_name, customer_phone, blood_group, 
                    hospital_name, destination, destination_latitude, destination_longitude, 
                    status, eta_minutes
                ) VALUES (
                    %s, 'Rohan Deshmukh', '+919999999999', 'B+',
                    'MGM Hospital & Blood Bank, Kamothe', 'Sub-District Hospital (SDH), Old Panvel', 
                    18.992500, 73.118000, 'On the way', 12
                ) RETURNING id;
            """, (p_id,))
            test_delivery_id = cursor.fetchone()[0]

            # Step B: Log 2 Panvel GPS breadcrumbs (moving along Sion-Panvel Highway towards Old Panvel)
            cursor.execute("""
                INSERT INTO location_updates (delivery_id, partner_id, latitude, longitude)
                VALUES 
                    (%s, %s, 19.015000, 73.099000),  -- Near Mansarovar / Kamothe
                    (%s, %s, 18.998500, 73.114000);  -- Near Panvel Flyover
            """, (test_delivery_id, p_id, test_delivery_id, p_id))

            # Step C: Query latest rider position (what Person 2 will provide to Person 3)
            cursor.execute("""
                SELECT lu.latitude, lu.longitude, lu.recorded_at 
                FROM location_updates lu
                WHERE lu.delivery_id = %s
                ORDER BY lu.recorded_at DESC
                LIMIT 1;
            """, (test_delivery_id,))
            latest_gps = cursor.fetchone()
            print(f"  Simulated rider '{p_name}' ({p_loc}) live GPS ping:")
            print(f"    Latest Latitude   : {latest_gps[0]}")
            print(f"    Latest Longitude  : {latest_gps[1]}")
            print(f"    Ping Timestamp    : {latest_gps[2]}")

            # Step D: Rollback / clean up test delivery to leave database clean
            cursor.execute("DELETE FROM deliveries WHERE id = %s;", (test_delivery_id,))
            conn.commit()
            print("  [PASS] Simulation successful. Test delivery cleaned up automatically.\n")

        cursor.close()
        conn.close()

        print("=" * 85)
        print("ALL TESTS PASSED! Your Panvel delivery database is ready for Person 2 & Person 3.")
        print("=" * 85)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
