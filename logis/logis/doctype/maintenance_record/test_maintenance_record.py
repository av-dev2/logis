# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate

from logis.tests.utils import (
	get_or_create_truck,
	receive_opening_stock,
	setup_stock_fixtures,
)

# The test site has no `payments` app; see test_logistic_settings.py.
IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Truck",
	"Trailer",
	"Company",
	"Item",
	"Maintenance Request",
	"UOM",
	"Stock Entry",
]


class IntegrationTestMaintenanceRecord(IntegrationTestCase):
	def setUp(self):
		# Each test gets its own truck so a submitted (and therefore
		# non-rolled-back-until-teardown) Maintenance Request from one test
		# can never be picked up by MaintenanceRecord.get_spares() in another.
		plate = f"T-MREC-{frappe.generate_hash(length=6)}"
		self.truck = get_or_create_truck(license_plate=plate)

	def test_missing_vehicle_raises_on_insert(self):
		doc = frappe.get_doc({"doctype": "Maintenance Record", "date_requested": nowdate()})

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_before_insert_pulls_spares_from_in_progress_request(self):
		# Maintenance Record.get_spares() copies rows from the linked
		# Maintenance Request's "Maintenance Spare Detail" children, which
		# have no `remained_qty` field of their own (only spare/uom/
		# qty_requested/qty_provided). A freshly pulled spare has qty_used=0,
		# so its remaining quantity equals qty_provided.
		spare = setup_stock_fixtures()["spare_item"].name
		request = frappe.get_doc(
			{
				"doctype": "Maintenance Request",
				"truck": self.truck.name,
				"posting_date": nowdate(),
				"spares": [{"spare": spare, "uom": "Nos", "qty_requested": 3, "qty_provided": 3}],
			}
		)
		request.insert()
		request.submit()  # sets status to "In Progress"

		record = frappe.get_doc(
			{
				"doctype": "Maintenance Record",
				"truck": self.truck.name,
				"date_requested": nowdate(),
			}
		)
		record.insert()

		self.assertEqual(len(record.spares), 1)
		self.assertEqual(record.spares[0].spare, spare)
		self.assertEqual(record.spares[0].qty_provided, 3)
		self.assertEqual(record.spares[0].qty_used, 0)
		self.assertEqual(record.spares[0].remained_qty, 3)

	def test_set_remained_qty_rejects_over_usage(self):
		doc = frappe.get_doc(
			{"doctype": "Maintenance Record", "truck": self.truck.name, "date_requested": nowdate()}
		)
		doc.insert()
		doc.append(
			"spares",
			{"spare": setup_stock_fixtures()["spare_item"].name, "qty_provided": 1, "qty_used": 5},
		)

		self.assertRaises(frappe.ValidationError, doc.save)

	def test_set_remained_qty_computes_remainder(self):
		doc = frappe.get_doc(
			{"doctype": "Maintenance Record", "truck": self.truck.name, "date_requested": nowdate()}
		)
		doc.insert()
		doc.append(
			"spares",
			{"spare": setup_stock_fixtures()["spare_item"].name, "qty_provided": 5, "qty_used": 2},
		)
		doc.save()

		self.assertEqual(doc.spares[0].remained_qty, 3)

	def test_create_material_transfer_requires_spares(self):
		doc = frappe.get_doc(
			{"doctype": "Maintenance Record", "truck": self.truck.name, "date_requested": nowdate()}
		)
		doc.insert()

		self.assertRaises(frappe.ValidationError, doc.create_material_transfer)

	def test_create_material_transfer_happy_path(self):
		fixtures = setup_stock_fixtures()
		receive_opening_stock(
			self,
			fixtures["spare_item"],
			fixtures["work_warehouse"],
			company=fixtures["company"].name,
			truck=self.truck.name,
		)

		doc = frappe.get_doc(
			{"doctype": "Maintenance Record", "truck": self.truck.name, "date_requested": nowdate()}
		)
		doc.insert()
		doc.append(
			"spares",
			{"spare": fixtures["spare_item"].name, "qty_provided": 2, "qty_used": 0},
		)
		doc.save()

		stock_entry_name = doc.create_material_transfer()

		self.assertTrue(frappe.db.exists("Stock Entry", stock_entry_name))
		self.assertEqual(doc.material_transfer, stock_entry_name)
