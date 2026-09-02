# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate

from logis.tests.utils import (
	get_or_create_driver,
	get_or_create_trailer,
	get_or_create_truck,
	setup_stock_fixtures,
)

# The test site has no `payments` app; see test_logistic_settings.py.
IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Truck",
	"Trailer",
	"Driver",
	"Item",
	"Company",
	"Supplier",
	"Stock Entry",
	"Truck Entry",
]


class IntegrationTestTripAssignment(IntegrationTestCase):
	def setUp(self):
		self.fixtures = setup_stock_fixtures()
		self.truck = get_or_create_truck()
		self.trailer = get_or_create_trailer()
		self.driver = get_or_create_driver()

	def new_assignment(self, **kwargs):
		data = {
			"doctype": "Trip Assignment",
			"truck": self.truck.name,
			"trailer": self.trailer.name,
			"driver": self.driver.name,
			"expected_trips": 5,
			"fuel_per_trip": 20,
			"fuel_type": self.fixtures["fuel_item"].name,
			"posting_date": nowdate(),
		}
		data.update(kwargs)
		return frappe.get_doc(data)

	def test_missing_required_fields_raises(self):
		doc = frappe.get_doc({"doctype": "Trip Assignment"})

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_set_total_fuel_on_save(self):
		doc = self.new_assignment(expected_trips=5, fuel_per_trip=20)
		doc.insert()

		# requested_fuel = fuel_per_trip * expected_trips - previous_remained_fuel(0)
		self.assertEqual(doc.todays_requested_fuel, 100)
		self.assertEqual(doc.total_fuel, 100)

	def test_set_total_expense_sums_expense_rows(self):
		supplier = frappe.get_doc(
			{"doctype": "Supplier", "supplier_name": "Trip Test Supplier", "supplier_type": "Company"}
		)
		if not frappe.db.exists("Supplier", "Trip Test Supplier"):
			supplier.insert(ignore_permissions=True)

		doc = self.new_assignment(
			expenses=[
				{
					"expense_name": self.fixtures["spare_item"].name,
					"amount": 30,
					"supplier": "Trip Test Supplier",
				},
				{
					"expense_name": self.fixtures["sales_item"].name,
					"amount": 20,
					"supplier": "Trip Test Supplier",
				},
			]
		)
		doc.insert()

		self.assertEqual(doc.total_expense, 50)

	def test_fetch_pfuel_values_from_latest_submitted_settlement(self):
		# No submitted Trip Settlement exists for this truck yet, so previous
		# issued/remained fuel should remain at their defaults (0/unset).
		doc = self.new_assignment()
		doc.insert()

		self.assertEqual(doc.previous_remained_fuel or 0, 0)
