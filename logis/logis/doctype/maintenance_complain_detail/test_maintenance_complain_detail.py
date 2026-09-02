# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from logis.tests.utils import get_or_create_truck

IGNORE_TEST_RECORD_DEPENDENCIES = ["Truck", "Trailer", "Company", "Item", "Stock Entry"]


class IntegrationTestMaintenanceComplainDetail(IntegrationTestCase):
	"""Maintenance Complain Detail is a child table of Maintenance Request."""

	def test_complain_row_has_no_mandatory_fields(self):
		truck = get_or_create_truck(license_plate=f"T-MCD-{frappe.generate_hash(length=6)}")
		doc = frappe.get_doc(
			{
				"doctype": "Maintenance Request",
				"truck": truck.name,
				"no_spare_required": 1,
				"complains": [{"complain": "Engine makes unusual noise"}],
			}
		)
		doc.insert()

		self.assertEqual(len(doc.complains), 1)
		self.assertEqual(doc.complains[0].complain, "Engine makes unusual noise")
