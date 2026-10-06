"""
BloodLink - BTech 2nd-Year Mini Project
Flask Backend for Blood Availability and Hospital Request System
Flow: Home -> Find Blood Form -> User Details -> Closest Hospitals with Availability -> Request Blood -> Thank You
"""

import os
import csv
import math
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(
    __name__,
    template_folder='.',     # Load templates from root directory
    static_folder='.',       # Serve CSS, JS, images, webfonts from root directory
    static_url_path=''       # Relative static paths work as-is
)
app.secret_key = 'bloodlink-btech-secret-key'

# Valid standard blood groups
VALID_BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# Paths to the CSV datasets
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
INVENTORY_CSV = os.path.join(DATA_DIR, 'BloodLink_Blood_Inventory.csv')
HOSPITALS_CSV = os.path.join(DATA_DIR, 'BloodLink_Hospitals.csv')

# Coordinate reference mapping for common Panvel / Navi Mumbai localities
LOCATION_COORDS = {
    "panvel": (18.9895, 73.1190),
    "old panvel": (18.9917, 73.1102),
    "new panvel": (18.9990, 73.1180),
    "khanda": (18.9975, 73.1010),
    "khanda colony": (18.9975, 73.1010),
    "kharghar": (19.0474, 73.0664),
    "kamothe": (19.0186, 73.0952),
    "lodhivali": (18.9500, 73.2200),
    "vichumbe": (18.9700, 73.1400),
    "sector 19": (19.0005, 73.1200),
    "sector 15": (18.9990, 73.1220),
    "sector 8": (18.9950, 73.1160),
    "sector 6": (18.9975, 73.1010),
    "uran road": (18.9895, 73.1105),
    "station": (18.9922, 73.1095)
}
DEFAULT_USER_COORDS = (18.9900, 73.1150)  # Central Panvel fallback coordinates


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points on the Earth (in km)
    using the Haversine formula.
    """
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except (ValueError, TypeError):
        return None

    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 1)


def resolve_location_coords(location_str, user_lat=None, user_lon=None):
    """
    Resolves geographic coordinates from either user geolocation or entered text location.
    """
    if user_lat and user_lon:
        try:
            return float(user_lat), float(user_lon)
        except (ValueError, TypeError):
            pass

    if not location_str:
        return DEFAULT_USER_COORDS

    clean_loc = location_str.strip().lower()
    for key, coords in LOCATION_COORDS.items():
        if key in clean_loc:
            return coords

    return DEFAULT_USER_COORDS


def get_csv_path(filename):
    """Finds CSV file in data/ or root directory."""
    path_in_data = os.path.join(DATA_DIR, filename)
    if os.path.exists(path_in_data):
        return path_in_data
    path_in_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(path_in_root):
        return path_in_root
    return None


def load_hospitals():
    """
    Loads hospitals dataset from BloodLink_Hospitals.csv.
    Columns: hospital_id, hospital_name, address, latitude, longitude, phone
    """
    csv_path = get_csv_path('BloodLink_Hospitals.csv')
    if not csv_path or not os.path.exists(csv_path):
        print("[ERROR] BloodLink_Hospitals.csv not found!")
        return {}

    hospitals = {}
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
                h_id = clean_row.get('hospital_id')
                if h_id:
                    hospitals[h_id] = {
                        'hospital_id': h_id,
                        'hospital_name': clean_row.get('hospital_name', 'Unknown Hospital'),
                        'address': clean_row.get('address', 'Address not available'),
                        'latitude': clean_row.get('latitude', ''),
                        'longitude': clean_row.get('longitude', ''),
                        'phone': clean_row.get('phone', 'N/A')
                    }
    except Exception as e:
        print(f"[ERROR] Failed to load hospitals CSV: {e}")
        return {}

    return hospitals


def load_blood_inventory():
    """
    Loads blood inventory dataset from BloodLink_Blood_Inventory.csv.
    Columns: inventory_id, hospital_id, blood_group, units, status
    """
    csv_path = get_csv_path('BloodLink_Blood_Inventory.csv')
    if not csv_path or not os.path.exists(csv_path):
        print("[ERROR] BloodLink_Blood_Inventory.csv not found!")
        return []

    inventory = []
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
                inventory.append(clean_row)
    except Exception as e:
        print(f"[ERROR] Failed to load inventory CSV: {e}")
        return []

    return inventory


def search_closest_hospitals(blood_group, location_str="", user_lat=None, user_lon=None, units_needed=1):
    """
    Searches inventory for the requested blood group, joins with hospital details,
    calculates distance from user location, and sorts results from closest to farthest.
    """
    hospitals_map = load_hospitals()
    inventory_items = load_blood_inventory()

    if not hospitals_map or not inventory_items:
        return []

    target_group = blood_group.strip().upper()
    user_coords = resolve_location_coords(location_str, user_lat, user_lon)

    matching_results = []

    for item in inventory_items:
        item_group = item.get('blood_group', '').strip().upper()
        if item_group == target_group:
            status = item.get('status', '').strip()
            try:
                units = int(item.get('units', 0))
            except ValueError:
                units = 0

            # Only available hospitals where units > 0 and status is not 'Not Available'
            if units > 0 and status.lower() != 'not available':
                h_id = item.get('hospital_id', '').strip()
                hospital_info = hospitals_map.get(h_id)

                if hospital_info:
                    dist = haversine_distance(
                        user_coords[0], user_coords[1],
                        hospital_info.get('latitude'), hospital_info.get('longitude')
                    )
                    distance_display = f"{dist} km" if dist is not None else "Nearby"
                    distance_sort_key = dist if dist is not None else 999.0

                    result = {
                        'hospital_id': h_id,
                        'hospital_name': hospital_info['hospital_name'],
                        'address': hospital_info['address'],
                        'phone': hospital_info['phone'],
                        'latitude': hospital_info['latitude'],
                        'longitude': hospital_info['longitude'],
                        'blood_group': target_group,
                        'units': units,
                        'status': status,
                        'distance': distance_display,
                        'distance_num': distance_sort_key
                    }
                    matching_results.append(result)

    # Sort results by distance ascending (closest first)
    matching_results.sort(key=lambda x: (x['distance_num'], -x['units']))
    return matching_results


# -------------------------------------------------------------
# Flask Routes
# -------------------------------------------------------------

@app.route('/')
def home():
    """Step 0: Home page route."""
    return render_template('index.html', valid_blood_groups=VALID_BLOOD_GROUPS)


@app.route('/about')
def about():
    """About Us page route."""
    return render_template('about.html')


@app.route('/find-blood', methods=['GET', 'POST'])
def find_blood():
    """
    Step 1: Blood Requirement Form.
    Collects: Blood Group, Urgency Level, Location, Units required.
    """
    if request.method == 'POST':
        blood_group = request.form.get('blood_group', '').strip().upper()
        urgency = request.form.get('urgency', 'Urgent').strip()
        location = request.form.get('location', '').strip()
        units = request.form.get('units', '1').strip()
        date_needed = request.form.get('date_needed', '').strip()
        time_needed = request.form.get('time_needed', '').strip()
        user_lat = request.form.get('user_lat', '').strip()
        user_lon = request.form.get('user_lon', '').strip()

        if not blood_group or blood_group not in VALID_BLOOD_GROUPS:
            flash("Please select a valid blood group.", "danger")
            return render_template('find-blood.html', valid_blood_groups=VALID_BLOOD_GROUPS)

        # Pass requirements forward to Step 2: User Details
        return render_template(
            'login.html',
            blood_group=blood_group,
            urgency=urgency,
            location=location,
            units=units,
            date_needed=date_needed,
            time_needed=time_needed,
            user_lat=user_lat,
            user_lon=user_lon
        )

    return render_template('find-blood.html', valid_blood_groups=VALID_BLOOD_GROUPS)


@app.route('/user-details', methods=['GET', 'POST'])
def user_details():
    """
    Step 2: User Contact Details Form (Name, Phone, optional Email).
    When submitted, routes to the closest available hospitals.
    """
    if request.method == 'POST':
        blood_group = request.form.get('blood_group', '').strip().upper()
        urgency = request.form.get('urgency', 'Urgent').strip()
        location = request.form.get('location', '').strip()
        units = request.form.get('units', '1').strip()
        user_lat = request.form.get('user_lat', '').strip()
        user_lon = request.form.get('user_lon', '').strip()

        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()

        # If name or phone are provided, proceed to closest hospitals
        if name and phone:
            return show_closest_hospitals(
                blood_group=blood_group,
                urgency=urgency,
                location=location,
                units=units,
                name=name,
                phone=phone,
                email=email,
                user_lat=user_lat,
                user_lon=user_lon
            )

        # Otherwise render form asking for details
        return render_template(
            'login.html',
            blood_group=blood_group,
            urgency=urgency,
            location=location,
            units=units,
            user_lat=user_lat,
            user_lon=user_lon
        )

    # GET request fallback
    return render_template('login.html', valid_blood_groups=VALID_BLOOD_GROUPS)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Alias route for the user details / login step."""
    return user_details()


def show_closest_hospitals(blood_group, urgency, location, units, name, phone, email, user_lat=None, user_lon=None):
    """
    Step 3: Searches and displays closest hospitals with required availability.
    """
    try:
        units_needed = int(units)
    except ValueError:
        units_needed = 1

    hospitals = search_closest_hospitals(
        blood_group=blood_group,
        location_str=location,
        user_lat=user_lat,
        user_lon=user_lon,
        units_needed=units_needed
    )

    return render_template(
        'availability.html',
        blood_group=blood_group,
        urgency=urgency,
        location=location or "Panvel",
        units=units,
        patient_name=name,
        contact_number=phone,
        email=email,
        hospitals=hospitals,
        total_found=len(hospitals),
        valid_blood_groups=VALID_BLOOD_GROUPS
    )


@app.route('/availability', methods=['GET', 'POST'])
def availability():
    """
    Direct route to availability page.
    Supports both GET search and POST from user contact details.
    """
    if request.method == 'POST':
        return user_details()

    # GET request - direct search
    blood_group = request.args.get('blood_group', '').strip().upper()
    location = request.args.get('location', '').strip()
    urgency = request.args.get('urgency', 'Urgent').strip()
    units = request.args.get('units', '1').strip()
    name = request.args.get('name', '').strip()
    phone = request.args.get('phone', '').strip()
    email = request.args.get('email', '').strip()

    error_message = None
    results = []

    if not blood_group:
        error_message = "Please select a blood group to check availability."
    elif blood_group not in VALID_BLOOD_GROUPS:
        error_message = f"Invalid blood group '{blood_group}'."
    else:
        results = search_closest_hospitals(blood_group, location)

    return render_template(
        'availability.html',
        blood_group=blood_group,
        location=location or "Panvel",
        urgency=urgency,
        units=units,
        patient_name=name,
        contact_number=phone,
        email=email,
        hospitals=results,
        total_found=len(results),
        error_message=error_message,
        valid_blood_groups=VALID_BLOOD_GROUPS
    )


@app.route('/request-blood', methods=['POST'])
def request_blood():
    """
    Step 4: Submits the blood request for the chosen hospital and shows confirmation.
    """
    hospital_id = request.form.get('hospital_id', '').strip()
    blood_group = request.form.get('blood_group', '').strip().upper()
    patient_name = request.form.get('name', '').strip()
    contact_number = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    units_needed = request.form.get('units', '1').strip()
    urgency = request.form.get('urgency', 'Urgent').strip()
    location = request.form.get('location', '').strip()
    distance = request.form.get('distance', '').strip()

    hospitals_map = load_hospitals()
    hospital_info = hospitals_map.get(hospital_id, {})
    hospital_name = hospital_info.get('hospital_name', 'Selected Hospital')

    return render_template(
        'thankyou.html',
        success=True,
        patient_name=patient_name,
        contact_number=contact_number,
        email=email,
        blood_group=blood_group,
        hospital_name=hospital_name,
        hospital_address=hospital_info.get('address', ''),
        hospital_phone=hospital_info.get('phone', ''),
        units=units_needed,
        urgency=urgency,
        location=location,
        distance=distance
    )


@app.route('/thankyou')
def thankyou():
    """Thank you confirmation page."""
    return render_template('thankyou.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error_message="Page not found. Redirected to Home."), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('index.html', error_message="An internal server error occurred."), 500

if __name__ == "__main__":
    print("==================================================")
    print("  Starting BloodLink Flask Web Application...")
    print("  Open your browser at: http://127.0.0.1:5001/")
    print("==================================================")
    app.run(debug=True, port=5001)
