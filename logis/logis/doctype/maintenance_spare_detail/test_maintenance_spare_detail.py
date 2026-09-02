# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from logis.tests.utils import get_or_create_truck, setup_stock_fixtures

IGNORE_TEST_RECORD_DEPENDENCIES = ["Truck", "Trailer", "Company", "Item", "Stock Entry"]


class IntegrationTestMaintenanceSpareDetail(IntegrationTestCase):
	"""Maintenance Spare Detail is a child table of Maintenance Request.

	See test_maintenance_request.py for duplicate-spare and stock-entry
	behavior that depends on this table.
	"""

	def test_spare_link_is_mandatory(self):
		truck = get_or_create_truck(license_plate=f"T-MSD-{frappe.generate_hash(length=6)}")
		doc = frappe.get_doc(
			{
				"doctype": "Maintenance Request",
				"truck": truck.name,
				"spares": [{"uom": "Nos", "qty_requested": 1}],
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_spare_row_persists(self):
		truck = get_or_create_truck(license_plate=f"T-MSD2-{frappe.generate_hash(length=6)}")
		spare = setup_stock_fixtures()["spare_item"].name
		doc = frappe.get_doc(
			{
				"doctype": "Maintenance Request",
				"truck": truck.name,
				"spares": [{"spare": spare, "uom": "Nos", "qty_requested": 2}],
			}
		)
		doc.insert()

		self.assertEqual(len(doc.spares), 1)
		self.assertEqual(doc.spares[0].spare, spare)
