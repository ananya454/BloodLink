"""
BloodLink - Automated Test Suite
Verifies data loading, distance calculation, closest hospital sorting, and complete 4-step user flow:
Home -> Find Blood Form -> User Details -> Closest Hospitals with Availability -> Request Blood -> Thank You
"""

import unittest
from app import (
    app,
    load_hospitals,
    load_blood_inventory,
    search_closest_hospitals,
    haversine_distance,
    VALID_BLOOD_GROUPS
)


class TestBloodLinkFlow(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_haversine_distance(self):
        # Distance between Old Panvel (18.9917, 73.1102) and Kharghar (19.0474, 73.0664)
        dist = haversine_distance(18.9917, 73.1102, 19.0474, 73.0664)
        self.assertIsNotNone(dist)
        self.assertGreater(dist, 5.0)
        self.assertLess(dist, 15.0)
        print(f"[PASS] Haversine distance Panvel to Kharghar: {dist} km")

    def test_search_closest_hospitals(self):
        # User in New Panvel searching for A+
        results = search_closest_hospitals("A+", location_str="New Panvel")
        self.assertGreater(len(results), 0, "Should find available hospitals for A+")
        # Verify sorted by distance
        distances = [r["distance_num"] for r in results]
        self.assertEqual(distances, sorted(distances), "Hospitals must be sorted by distance ascending")
        closest = results[0]
        self.assertIn("distance", closest)
        self.assertGreater(closest["units"], 0)
        print(f"[PASS] Closest hospital to New Panvel for A+: {closest['hospital_name']} at {closest['distance']} ({closest['units']} units in stock)")

    def test_step0_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn("Find Blood", content)
        self.assertIn("Every Drop Can Save a Life", content)
        print("[PASS] Step 0: Home page loaded with 'Find Blood' button.")

    def test_step1_find_blood_page(self):
        response = self.client.get('/find-blood')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn("Required Blood Group", content)
        self.assertIn("Urgency Level", content)
        self.assertIn("Your Location", content)
        self.assertIn("Units of Blood Required", content)
        print("[PASS] Step 1: Find Blood form loaded.")

    def test_step1_submit_to_user_details(self):
        # Submit blood requirements
        post_data = {
            'blood_group': 'B+',
            'urgency': 'Critical',
            'location': 'Khanda Colony',
            'units': '2'
        }
        response = self.client.post('/find-blood', data=post_data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn("Step 2: Enter Your Contact Details", content)
        self.assertIn("B+", content)
        self.assertIn("Critical", content)
        self.assertIn("Khanda Colony", content)
        self.assertIn("Patient / Requester Name", content)
        print("[PASS] Step 1 -> Step 2: Blood requirements passed to contact details form.")

    def test_step2_submit_to_closest_hospitals(self):
        # Submit contact details
        post_data = {
            'blood_group': 'B+',
            'urgency': 'Critical',
            'location': 'Khanda Colony',
            'units': '2',
            'name': 'Ananya Iyer',
            'phone': '9876543210',
            'email': 'ananya@example.com'
        }
        response = self.client.post('/user-details', data=post_data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn("Closest Hospitals for", content)
        self.assertIn("Available Hospitals (Sorted by Distance)", content)
        self.assertIn("Ananya Iyer", content)
        self.assertIn("Request Blood", content)
        print("[PASS] Step 2 -> Step 3: Closest hospitals with availability displayed.")

    def test_step3_request_blood_confirmation(self):
        # Submit final Request Blood for a specific hospital
        post_data = {
            'hospital_id': 'H002',
            'blood_group': 'B+',
            'name': 'Ananya Iyer',
            'phone': '9876543210',
            'email': 'ananya@example.com',
            'units': '2',
            'urgency': 'Critical',
            'location': 'Khanda Colony',
            'distance': '0.8 km'
        }
        response = self.client.post('/request-blood', data=post_data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn("Request Submitted Successfully!", content)
        self.assertIn("Ashtvinayak Hospital", content)
        self.assertIn("Ananya Iyer", content)
        self.assertIn("9876543210", content)
        self.assertIn("0.8 km", content)
        print("[PASS] Step 4: 'Request Blood' submitted and confirmation summary rendered.")


if __name__ == '__main__':
    unittest.main()
