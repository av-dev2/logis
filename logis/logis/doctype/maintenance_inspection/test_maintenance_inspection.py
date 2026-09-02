# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestMaintenanceInspection(IntegrationTestCase):
	def test_creation(self):
		doc = frappe.get_doc(
			{
				"doctype": "Maintenance Inspection",
				"inspection_name": "Tyre Pressure Check",
				"description": "Check tyre pressure on all wheels",
			}
		)
		doc.insert()

		self.assertEqual(doc.name, "Tyre Pressure Check")

	def test_duplicate_inspection_name_not_allowed(self):
		frappe.get_doc({"doctype": "Maintenance Inspection", "inspection_name": "Brake Test"}).insert()

		duplicate = frappe.get_doc({"doctype": "Maintenance Inspection", "inspection_name": "Brake Test"})
		self.assertRaises(frappe.DuplicateEntryError, duplicate.insert)
