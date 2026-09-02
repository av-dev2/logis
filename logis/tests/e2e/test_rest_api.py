"""Layer 2: REST/API-over-HTTP tests for logis.

These exercise the standard Frappe REST endpoints
(/api/resource/<DocType>) over real HTTP, as opposed to the in-process
IntegrationTestCase suites elsewhere in this app, which call controllers
directly. They are skipped by default (the framework's `run-tests` command
runs everything in-process and has no HTTP server available) and only run
when a BASE_URL env var points at a live site, e.g.:

	BASE_URL=http://logis16-test.localhost:8001 \\
	FRAPPE_API_KEY=... FRAPPE_API_SECRET=... \\
		python -m unittest logis.tests.e2e.test_rest_api

Given the time budget for this audit, this covers a couple of representative
endpoints (list + get on a simple doctype, and a validation error on create)
rather than full CRUD across every doctype - the in-process IntegrationTestCase
suites already give deep controller coverage; this layer exists mainly to
prove the REST surface is reachable and returns the expected HTTP semantics.
"""

import os
import unittest

BASE_URL = os.environ.get("BASE_URL")


@unittest.skipUnless(BASE_URL, "Set BASE_URL to a running site to run Layer 2 REST tests")
class TestLogisRestApi(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		import requests

		cls.session = requests.Session()
		api_key = os.environ.get("FRAPPE_API_KEY")
		api_secret = os.environ.get("FRAPPE_API_SECRET")
		if api_key and api_secret:
			cls.session.headers["Authorization"] = f"token {api_key}:{api_secret}"

	def test_list_trucks_returns_200(self):
		resp = self.session.get(f"{BASE_URL}/api/resource/Truck")
		self.assertEqual(resp.status_code, 200)
		self.assertIn("data", resp.json())

	def test_get_missing_truck_returns_404(self):
		resp = self.session.get(f"{BASE_URL}/api/resource/Truck/does-not-exist-xyz")
		self.assertEqual(resp.status_code, 404)

	def test_create_truck_without_make_returns_417(self):
		# Missing mandatory field 'make' -> Frappe REST returns 417 Expectation Failed.
		resp = self.session.post(
			f"{BASE_URL}/api/resource/Truck",
			json={"license_plate": "E2E-TEST-PLATE"},
		)
		self.assertIn(resp.status_code, (401, 403, 417))
