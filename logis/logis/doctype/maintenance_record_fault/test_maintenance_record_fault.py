# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate

from logis.tests.utils import get_or_create_truck

IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Truck",
	"Trailer",
	"Company",
	"Item",
	"Maintenance Request",
	"UOM",
	"Maintenance Fault Type",
]


class IntegrationTestMaintenanceRecordFault(IntegrationTestCase):
	"""Maintenance Record Fault is a child table of Maintenance Record."""

	def setUp(self):
		self.truck = get_or_create_truck(license_plate=f"T-MRF-{frappe.generate_hash(length=6)}")
		self.fault_type = "Suspension Fault"
		if not frappe.db.exists("Maintenance Fault Type", self.fault_type):
			frappe.get_doc({"doctype": "Maintenance Fault Type", "fault_type": self.fault_type}).insert()

	def test_fault_type_is_mandatory(self):
		doc = frappe.get_doc(
			{
				"doctype": "Maintenance Record",
				"truck": self.truck.name,
				"date_requested": nowdate(),
				"faults": [{"description": "Missing fault type"}],
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_status_defaults_and_row_persists(self):
		doc = frappe.get_doc(
			{
				"doctype": "Maintenance Record",
				"truck": self.truck.name,
				"date_requested": nowdate(),
				"faults": [{"fault_type": self.fault_type, "description": "Rear suspension noise"}],
			}
		)
		doc.insert()

		self.assertEqual(len(doc.faults), 1)
		self.assertEqual(doc.faults[0].fault_type, self.fault_type)
