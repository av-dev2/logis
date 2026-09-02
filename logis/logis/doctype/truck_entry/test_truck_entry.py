# Copyright (c) 2025, Administrator and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestTruckEntry(IntegrationTestCase):
	"""Integration tests for Truck Entry."""

	def test_truck_entry_creation(self):
		doc = frappe.get_doc({"doctype": "Truck Entry", "truck_name": "TE-001/TR-001"})
		doc.insert()

		self.assertEqual(doc.doctype, "Truck Entry")
		self.assertEqual(doc.name, "TE-001/TR-001")

	def test_missing_truck_name_raises(self):
		doc = frappe.get_doc({"doctype": "Truck Entry"})

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_duplicate_truck_name_not_allowed(self):
		frappe.get_doc({"doctype": "Truck Entry", "truck_name": "TE-DUP/TR-DUP"}).insert()

		duplicate = frappe.get_doc({"doctype": "Truck Entry", "truck_name": "TE-DUP/TR-DUP"})
		self.assertRaises(frappe.DuplicateEntryError, duplicate.insert)
