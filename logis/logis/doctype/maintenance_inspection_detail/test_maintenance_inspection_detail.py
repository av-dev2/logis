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
	"Maintenance Inspection",
]


class IntegrationTestMaintenanceInspectionDetail(IntegrationTestCase):
	"""Maintenance Inspection Detail is a child table of Maintenance Request."""

	def test_inspection_row_persists(self):
		truck = get_or_create_truck(license_plate=f"T-MID-{frappe.generate_hash(length=6)}")
		inspection_name = "Brake Pad Check"
		if not frappe.db.exists("Maintenance Inspection", inspection_name):
			frappe.get_doc({"doctype": "Maintenance Inspection", "inspection_name": inspection_name}).insert()

		doc = frappe.get_doc(
			{
				"doctype": "Maintenance Request",
				"truck": truck.name,
				"no_spare_required": 1,
				"inspections": [{"inspection_name": inspection_name, "description": "Worn brake pads"}],
			}
		)
		doc.insert()

		self.assertEqual(len(doc.inspections), 1)
		self.assertEqual(doc.inspections[0].inspection_name, inspection_name)
