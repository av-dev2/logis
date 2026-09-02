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

# The test site has no `payments` app; see test_logistic_settings.py.
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


class IntegrationTestTripSettlement(IntegrationTestCase):
	def setUp(self):
		self.fixtures = setup_stock_fixtures()
		self.truck = get_or_create_truck(license_plate=f"T-TS-{frappe.generate_hash(length=6)}")
		self.trailer = get_or_create_trailer(license_plate=f"TR-TS-{frappe.generate_hash(length=6)}")
		self.driver = get_or_create_driver()
		self.customer = get_or_create_customer()
		self.assignment = frappe.get_doc(
			{
				"doctype": "Trip Assignment",
				"truck": self.truck.name,
				"trailer": self.trailer.name,
				"driver": self.driver.name,
				"expected_trips": 2,
				"fuel_per_trip": 10,
				"fuel_type": self.fixtures["fuel_item"].name,
				"posting_date": nowdate(),
			}
		)
		self.assignment.insert()

	def new_settlement(self, **kwargs):
		# NOTE: `fuel_provided` and `fuel_per_each_trip` are `fetch_from`
		# trip_assignment.total_fuel / trip_assignment.fuel_per_trip, so
		# whatever is passed here is silently overwritten on save - don't
		# set them, assert against what the linked Trip Assignment produces.
		#
		# Trip Settlement's transaction also lives for the whole TestCase
		# class (rolled back only at class teardown), so movement orders
		# must be unique per call or validate_duplicate_movement_order()
		# will see them as clashing with an earlier test in this class.
		suffix = frappe.generate_hash(length=6)
		data = {
			"doctype": "Trip Settlement",
			"trip_assignment": self.assignment.name,
			"truck": self.truck.name,
			"trailer": self.trailer.name,
			"customer": self.customer.name,
			"trips": [
				{"movement_order": f"MO-{suffix}-1", "container_no": "CN-001", "amount": 100},
				{"movement_order": f"MO-{suffix}-2", "container_no": "CN-002", "amount": 150},
			],
		}
		data.update(kwargs)
		return frappe.get_doc(data)

	def test_missing_required_fields_raises(self):
		# set_total_fuel_provided() and set_total_income() treat missing
		# numeric fields (fuel_per_each_trip, fuel_provided, row.amount) as 0
		# so the totals computation itself never crashes, letting the normal
		# mandatory-field validation surface first.
		doc = frappe.get_doc({"doctype": "Trip Settlement"})

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_set_total_income_sums_trip_rows(self):
		doc = self.new_settlement()
		doc.insert()

		self.assertEqual(doc.total_income, 250)

	def test_set_total_fuel_provided_computes_consumption(self):
		doc = self.new_settlement()
		doc.insert()

		# fuel_per_each_trip/fuel_provided are fetched from the Trip
		# Assignment (fuel_per_trip=10, expected_trips=2 -> total_fuel=20).
		self.assertEqual(doc.no_of_trips, 2)
		self.assertEqual(doc.fuel_per_each_trip, 10)
		self.assertEqual(doc.fuel_consumed, 20)  # 2 trips * 10 fuel_per_each_trip
		self.assertEqual(doc.fuel_remained, 0)  # 20 provided - 20 consumed

	def test_duplicate_movement_order_across_settlements_raises(self):
		first = self.new_settlement(
			trips=[{"movement_order": "MO-DUP", "container_no": "CN-1", "amount": 100}]
		)
		first.insert()

		second_assignment = frappe.get_doc(
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
		second_assignment.insert()

		second = self.new_settlement(
			trip_assignment=second_assignment.name,
			trips=[{"movement_order": "MO-DUP", "container_no": "CN-2", "amount": 100}],
		)

		self.assertRaises(frappe.ValidationError, second.insert)
