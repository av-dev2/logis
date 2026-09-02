# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate

from logis.tests.utils import (
	get_or_create_driver,
	get_or_create_supplier,
	get_or_create_trailer,
	get_or_create_truck,
	setup_stock_fixtures,
)

IGNORE_TEST_RECORD_DEPENDENCIES = ["Truck", "Trailer", "Driver", "Item", "Company", "Supplier"]


class IntegrationTestTripAssignmentExpense(IntegrationTestCase):
	"""Trip Assignment Expense is a child table of Trip Assignment.

	See test_trip_assignment.py for the total_expense sum behavior.
	"""

	def new_assignment(self, **kwargs):
		fixtures = setup_stock_fixtures()
		data = {
			"doctype": "Trip Assignment",
			"truck": get_or_create_truck(license_plate=f"T-TAE-{frappe.generate_hash(length=6)}").name,
			"trailer": get_or_create_trailer(license_plate=f"TR-TAE-{frappe.generate_hash(length=6)}").name,
			"driver": get_or_create_driver().name,
			"expected_trips": 1,
			"fuel_per_trip": 10,
			"fuel_type": fixtures["fuel_item"].name,
			"posting_date": nowdate(),
		}
		data.update(kwargs)
		return frappe.get_doc(data)

	def test_expense_row_requires_amount_and_supplier(self):
		# Trip Assignment.set_total_expense() treats a missing `expense.amount`
		# as 0, so the totals computation itself never crashes and the normal
		# mandatory-field validation surfaces instead.
		spare = setup_stock_fixtures()["spare_item"].name
		doc = self.new_assignment(expenses=[{"expense_name": spare}])

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_expense_row_persists(self):
		spare = setup_stock_fixtures()["spare_item"].name
		supplier = get_or_create_supplier()
		doc = self.new_assignment(expenses=[{"expense_name": spare, "amount": 40, "supplier": supplier.name}])
		doc.insert()

		self.assertEqual(len(doc.expenses), 1)
		self.assertEqual(doc.expenses[0].amount, 40)
		self.assertEqual(doc.total_expense, 40)
