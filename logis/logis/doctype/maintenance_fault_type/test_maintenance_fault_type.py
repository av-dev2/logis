# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestMaintenanceFaultType(IntegrationTestCase):
	def test_creation(self):
		# NOTE: use a name that isn't in the seeded list from
		# logis.install.create_maintenance_fault_types() (e.g. "Engine
		# Overheating" already exists on any site that ran after_install),
		# or this collides with real data and raises DuplicateEntryError.
		doc = frappe.get_doc({"doctype": "Maintenance Fault Type", "fault_type": "Test-Only Custom Fault"})
		doc.insert()

		self.assertEqual(doc.name, "Test-Only Custom Fault")

	def test_missing_fault_type_raises(self):
		doc = frappe.get_doc({"doctype": "Maintenance Fault Type"})

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_duplicate_fault_type_not_allowed(self):
		frappe.get_doc({"doctype": "Maintenance Fault Type", "fault_type": "Brake Failure"}).insert()

		duplicate = frappe.get_doc({"doctype": "Maintenance Fault Type", "fault_type": "Brake Failure"})
		self.assertRaises(frappe.DuplicateEntryError, duplicate.insert)
