# Copyright (c) 2025, AV Dev and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase

from logis.tests.utils import (
	get_or_create_truck,
	receive_opening_stock,
	setup_stock_fixtures,
)

# The test site has no `payments` app, so the automatic test-record
# dependency walker crashes if allowed to recurse into Company/Item/Truck ->
# ... -> Payment Gateway. We supply our own fixtures instead.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Truck", "Trailer", "Company", "Item", "Stock Entry"]


class IntegrationTestMaintenanceRequest(IntegrationTestCase):
	def setUp(self):
		self.truck = get_or_create_truck()

	def new_request(self, **kwargs):
		data = {"doctype": "Maintenance Request", "truck": self.truck.name}
		data.update(kwargs)
		return frappe.get_doc(data)

	def test_no_vehicle_selected_raises_on_submit(self):
		doc = frappe.get_doc({"doctype": "Maintenance Request", "no_spare_required": 1})
		doc.insert()

		self.assertRaises(frappe.ValidationError, doc.submit)

	def test_status_defaults_to_pending_on_save(self):
		doc = self.new_request(no_spare_required=1)
		doc.insert()

		self.assertEqual(doc.status, "Pending")

	def test_spares_required_unless_no_spare_required(self):
		doc = self.new_request()

		self.assertRaises(frappe.ValidationError, doc.submit)

	def test_no_spare_required_clears_spares_table_on_submit(self):
		spare = setup_stock_fixtures()["spare_item"].name
		doc = self.new_request(
			no_spare_required=1,
			spares=[{"spare": spare, "uom": "Nos", "qty_requested": 2}],
		)
		doc.insert()
		self.assertEqual(len(doc.spares), 1, "spares are only cleared on submit, not on save")

		doc.submit()
		self.assertEqual(len(doc.spares), 0)

	def test_duplicate_spares_raise_on_save(self):
		spare = setup_stock_fixtures()["spare_item"].name
		doc = self.new_request(
			spares=[
				{"spare": spare, "uom": "Nos", "qty_requested": 2},
				{"spare": spare, "uom": "Nos", "qty_requested": 3},
			]
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_create_stock_entry_requires_spares(self):
		doc = self.new_request(no_spare_required=1)
		doc.insert()

		self.assertRaises(frappe.ValidationError, doc.create_stock_entry)

	def test_create_stock_entry_happy_path(self):
		fixtures = setup_stock_fixtures()
		receive_opening_stock(
			self, fixtures["spare_item"], fixtures["main_warehouse"], company=fixtures["company"].name
		)
		doc = self.new_request(
			spares=[{"spare": fixtures["spare_item"].name, "uom": "Nos", "qty_requested": 5}],
		)
		doc.insert()

		stock_entry_name = doc.create_stock_entry()

		self.assertTrue(frappe.db.exists("Stock Entry", stock_entry_name))
		self.assertEqual(doc.stock_entry, stock_entry_name)

	def test_on_cancel_sets_status_cancelled(self):
		fixtures = setup_stock_fixtures()
		receive_opening_stock(
			self, fixtures["spare_item"], fixtures["main_warehouse"], company=fixtures["company"].name
		)
		doc = self.new_request(
			spares=[{"spare": fixtures["spare_item"].name, "uom": "Nos", "qty_requested": 1}],
		)
		doc.insert()
		doc.create_stock_entry()
		stock_entry = frappe.get_doc("Stock Entry", doc.stock_entry)
		stock_entry.submit()
		doc.reload()

		doc.submit()
		self.assertEqual(doc.status, "In Progress")

		doc.cancel()
		self.assertEqual(doc.status, "Cancelled")
