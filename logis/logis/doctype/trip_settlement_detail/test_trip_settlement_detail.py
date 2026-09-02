# Copyright (c) 2025, Administrator and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate

from logis.tests.utils import (
	get_or_create_customer,
	get_or_create_driver,
	get_or_create_trailer,
	get_or_create_truck,
	setup_stock_fixtures,
)

# Trip Settlement Detail is a child table of Trip Settlement and is only
# meaningful in that context; see test_trip_settlement.py for the parent's
# controller-level coverage. This file focuses on the row's own mandatory
# fields.
IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Trip Assignment",
	"Truck",
	"Trailer",
	"Driver",
	"Company",
	"Customer",
	"Truck Entry",
	"Stock Entry",
	"Sales Invoice",
]


class IntegrationTestTripSettlementDetail(IntegrationTestCase):
	def setUp(self):
		self.fixtures = setup_stock_fixtures()
		self.truck = get_or_create_truck(license_plate=f"T-TSD-{frappe.generate_hash(length=6)}")
		self.trailer = get_or_create_trailer(license_plate=f"TR-TSD-{frappe.generate_hash(length=6)}")
		self.driver = get_or_create_driver()
		self.customer = get_or_create_customer()
		self.assignment = frappe.get_doc(
			{
				"doctype": "Trip Assignment",
				"truck": self.truck.name,
				"trailer": self.trailer.name,
				"driver": self.driver.name,
				"expected_trips": 1,
				"fuel_per_trip": 10,
				"fuel_type": self.fixtures["fuel_item"].name,
				"posting_date": nowdate(),
			}
		)
		self.assignment.insert()

	def test_row_requires_movement_order_container_and_amount(self):
		# Trip Settlement.set_total_income() treats a missing `row.amount` as 0,
		# so the totals computation itself never crashes and the normal
		# mandatory-field validation surfaces instead.
		doc = frappe.get_doc(
			{
				"doctype": "Trip Settlement",
				"trip_assignment": self.assignment.name,
				"truck": self.truck.name,
				"trailer": self.trailer.name,
				"customer": self.customer.name,
				"trips": [{"movement_order": "MO-INCOMPLETE"}],
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_row_persists_with_all_fields(self):
		doc = frappe.get_doc(
			{
				"doctype": "Trip Settlement",
				"trip_assignment": self.assignment.name,
				"truck": self.truck.name,
				"trailer": self.trailer.name,
				"customer": self.customer.name,
				"trips": [{"movement_order": "MO-COMPLETE", "container_no": "CN-COMPLETE", "amount": 75}],
			}
		)
		doc.insert()

		self.assertEqual(len(doc.trips), 1)
		self.assertEqual(doc.trips[0].movement_order, "MO-COMPLETE")
		self.assertEqual(doc.trips[0].amount, 75)
