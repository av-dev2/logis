# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate

from logis.tests.utils import get_or_create_truck

IGNORE_TEST_RECORD_DEPENDENCIES = ["Truck", "Trailer", "Company", "Item", "Maintenance Request", "UOM"]


class IntegrationTestMaintenanceRecordDetail(IntegrationTestCase):
	"""Maintenance Record Detail is a child table of Maintenance Record.

	It is populated automatically by Maintenance Record.get_spares() (see
	before_insert), which overwrites anything set manually - so this checks
	the default (no matching in-progress request) rather than manual rows.
	"""

	def test_defaults_to_empty_when_no_matching_request(self):
		truck = get_or_create_truck(license_plate=f"T-MRD-{frappe.generate_hash(length=6)}")
		doc = frappe.get_doc(
			{"doctype": "Maintenance Record", "truck": truck.name, "date_requested": nowdate()}
		)
		doc.insert()

		self.assertEqual(len(doc.maintenance_requests), 0)
