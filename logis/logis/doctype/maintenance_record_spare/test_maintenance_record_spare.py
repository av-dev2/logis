# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate

from logis.tests.utils import get_or_create_truck, setup_stock_fixtures

IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Truck",
	"Trailer",
	"Company",
	"Item",
	"Maintenance Request",
	"UOM",
	"Stock Entry",
]


class IntegrationTestMaintenanceRecordSpare(IntegrationTestCase):
	"""Maintenance Record Spare is a child table of Maintenance Record.

	See test_maintenance_record.py for the qty_used/qty_provided/remained_qty
	arithmetic in Maintenance Record.set_remained_qty().
	"""

	def test_spare_link_is_mandatory(self):
		truck = get_or_create_truck(license_plate=f"T-MRS-{frappe.generate_hash(length=6)}")
		doc = frappe.get_doc(
			{"doctype": "Maintenance Record", "truck": truck.name, "date_requested": nowdate()}
		)
		doc.insert()
		doc.append("spares", {"qty_provided": 1, "qty_used": 0})

		self.assertRaises(frappe.MandatoryError, doc.save)

	def test_spare_row_persists(self):
		truck = get_or_create_truck(license_plate=f"T-MRS2-{frappe.generate_hash(length=6)}")
		spare = setup_stock_fixtures()["spare_item"].name
		doc = frappe.get_doc(
			{"doctype": "Maintenance Record", "truck": truck.name, "date_requested": nowdate()}
		)
		doc.insert()
		doc.append("spares", {"spare": spare, "qty_provided": 4, "qty_used": 1})
		doc.save()

		self.assertEqual(doc.spares[0].spare, spare)
		self.assertEqual(doc.spares[0].remained_qty, 3)
