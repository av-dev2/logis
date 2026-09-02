# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from logis.tests.utils import get_or_create_truck

IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Truck",
	"Trailer",
	"Company",
	"Item",
	"Stock Entry",
	"Maintenance Fault Type",
]


class IntegrationTestMaintenanceFaultDetail(IntegrationTestCase):
	"""Maintenance Fault Detail is a child table of Maintenance Request."""

	def setUp(self):
		self.truck = get_or_create_truck(license_plate=f"T-MFD-{frappe.generate_hash(length=6)}")
		self.fault_type = "Electrical Fault"
		if not frappe.db.exists("Maintenance Fault Type", self.fault_type):
			frappe.get_doc({"doctype": "Maintenance Fault Type", "fault_type": self.fault_type}).insert()

	def test_fault_type_is_mandatory(self):
		doc = frappe.get_doc(
			{
				"doctype": "Maintenance Request",
				"truck": self.truck.name,
				"no_spare_required": 1,
				"faults": [{"description": "Missing fault type"}],
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_fault_row_persists(self):
		doc = frappe.get_doc(
			{
				"doctype": "Maintenance Request",
				"truck": self.truck.name,
				"no_spare_required": 1,
				"faults": [{"fault_type": self.fault_type, "description": "Short circuit in dashboard"}],
			}
		)
		doc.insert()

		self.assertEqual(len(doc.faults), 1)
		self.assertEqual(doc.faults[0].fault_type, self.fault_type)
