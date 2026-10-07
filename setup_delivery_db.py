"""
BloodLink - Database Setup Script for Delivery & Real-Time Tracking Feature
Role: Person 1 (Database Developer)

Run this script directly in your VS Code terminal:
    python setup_delivery_db.py
"""

import os
import sys

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("\n" + "=" * 60)
    print("[ERROR] 'psycopg2' is not installed in your Python environment.")
    print("=" * 60)
    print("Run this command in your VS Code terminal:")
    print("    pip install psycopg2-binary python-dotenv")
    print("=" * 60 + "\n")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Database credentials (reads from .env or defaults to standard local postgres settings)
DB_NAME = os.getenv("DB_NAME", "bloodlink_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def run_sql_file(cursor, file_path):
    filename = os.path.basename(file_path)
    print(f"Executing: {filename}...")
    with open(file_path, "r", encoding="utf-8") as f:
        query = f.read()
        cursor.execute(query)

def main():
    print("=" * 70)
    print(" BloodLink: Delivery & Tracking Database Initializer")
    print("=" * 70)
    print(f"Target Database : {DB_NAME}")
    print(f"Host / Port     : {DB_HOST}:{DB_PORT}")
    print(f"User            : {DB_USER}")
    print("-" * 70)

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print("Connected to PostgreSQL successfully!\n")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_file = os.path.join(base_dir, "database", "delivery_schema.sql")
        seed_file = os.path.join(base_dir, "database", "seed_partners.sql")

        # Step 1: Run delivery schema
        run_sql_file(cursor, schema_file)
        print("  -> Created tables: 'delivery_partners', 'deliveries', 'location_updates'")
        print("  -> Applied indexes & foreign keys successfully.\n")

        # Step 2: Seed delivery partners
        run_sql_file(cursor, seed_file)
        print("  -> Seeded sample delivery partners with GPS coordinates.\n")

        # Step 3: Verify all 3 tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_name IN ('delivery_partners', 'deliveries', 'location_updates')
            ORDER BY table_name;
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]

        print("Verification Checklist:")
        for tbl in ['delivery_partners', 'deliveries', 'location_updates']:
            status = "[OK]" if tbl in existing_tables else "[MISSING]"
            print(f"  {status} Table: public.{tbl}")

        # Step 4: Show partner count
        cursor.execute("SELECT COUNT(*) FROM delivery_partners;")
        partner_count = cursor.fetchone()[0]
        print(f"\nTotal delivery partners seeded: {partner_count}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 70)
        print("SUCCESS! Database setup completed.")
        print("Now run 'python test_delivery_db.py' in VS Code to test queries.")
        print("=" * 70)

    except psycopg2.OperationalError as e:
        print("\n[DATABASE CONNECTION ERROR]")
        print("Could not connect to PostgreSQL. Please check:")
        print(f"1. Is PostgreSQL running on your machine?")
        print(f"2. Does the database '{DB_NAME}' exist in pgAdmin? (Create it if not)")
        print(f"3. Verify your DB password in your .env file.")
        print(f"\nDetails:\n{e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
