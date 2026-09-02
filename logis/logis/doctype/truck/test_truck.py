# Copyright (c) 2025, Administrator and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestTruck(IntegrationTestCase):
	"""Integration tests for Truck."""

	def test_truck_creation(self):
		doc = frappe.get_doc({"doctype": "Truck", "license_plate": "T 123 ABC", "make": "Scania"})
		doc.insert()

		self.assertEqual(doc.doctype, "Truck")
		self.assertEqual(doc.name, "T 123 ABC")

	def test_license_plate_is_the_name(self):
		doc = frappe.get_doc({"doctype": "Truck", "license_plate": "T 456 XYZ", "make": "Volvo"})
		doc.insert()

		self.assertEqual(doc.name, doc.license_plate)

	def test_missing_required_fields_raises(self):
		doc = frappe.get_doc({"doctype": "Truck", "license_plate": "T 789 QRS"})

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_duplicate_license_plate_not_allowed(self):
		frappe.get_doc({"doctype": "Truck", "license_plate": "T 999 DUP", "make": "Isuzu"}).insert()

		duplicate = frappe.get_doc({"doctype": "Truck", "license_plate": "T 999 DUP", "make": "Isuzu"})
		self.assertRaises(frappe.DuplicateEntryError, duplicate.insert)

	def test_after_insert_creates_vehicle(self):
		doc = frappe.get_doc(
			{"doctype": "Truck", "license_plate": "T 111 VEH", "make": "Man", "model": "TGS"}
		)
		doc.insert()

		self.assertTrue(frappe.db.exists("Vehicle", "T 111 VEH"))
		vehicle = frappe.get_doc("Vehicle", "T 111 VEH")
		self.assertEqual(vehicle.is_truck, 1)
		self.assertEqual(vehicle.is_trailer, 0)
