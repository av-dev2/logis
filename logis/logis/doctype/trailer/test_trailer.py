# Copyright (c) 2025, Administrator and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestTrailer(IntegrationTestCase):
	"""Integration tests for Trailer."""

	def test_trailer_creation(self):
		doc = frappe.get_doc({"doctype": "Trailer", "license_plate": "TR 123 ABC", "make": "Doepker"})
		doc.insert()

		self.assertEqual(doc.doctype, "Trailer")
		self.assertEqual(doc.name, "TR 123 ABC")

	def test_missing_required_fields_raises(self):
		doc = frappe.get_doc({"doctype": "Trailer", "license_plate": "TR 789 QRS"})

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_duplicate_license_plate_not_allowed(self):
		frappe.get_doc({"doctype": "Trailer", "license_plate": "TR 999 DUP", "make": "Fruehauf"}).insert()

		duplicate = frappe.get_doc({"doctype": "Trailer", "license_plate": "TR 999 DUP", "make": "Fruehauf"})
		self.assertRaises(frappe.DuplicateEntryError, duplicate.insert)

	def test_after_insert_creates_vehicle(self):
		doc = frappe.get_doc({"doctype": "Trailer", "license_plate": "TR 111 VEH", "make": "Doepker"})
		doc.insert()

		self.assertTrue(frappe.db.exists("Vehicle", "TR 111 VEH"))
		vehicle = frappe.get_doc("Vehicle", "TR 111 VEH")
		self.assertEqual(vehicle.is_trailer, 1)
		self.assertEqual(vehicle.is_truck, 0)
