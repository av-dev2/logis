# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from logis.tests.utils import setup_stock_fixtures

# The v16 test site has no `payments` app installed, so frappe's automatic
# test-record dependency walker explodes into "DocType Payment Gateway not
# found" once it reaches Warehouse/Item -> ... -> Payment Gateway Account.
# We provide our own fixtures (see logis.tests.utils) instead.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Warehouse", "Item"]


class IntegrationTestLogisticSettings(IntegrationTestCase):
	def test_is_a_single_doctype(self):
		meta = frappe.get_meta("Logistic Settings")
		self.assertEqual(meta.issingle, 1)

	def test_save_with_required_links(self):
		fixtures = setup_stock_fixtures()
		settings = frappe.get_single("Logistic Settings")

		self.assertEqual(settings.main_warehouse, fixtures["main_warehouse"].name)
		self.assertEqual(settings.work_warehouse, fixtures["work_warehouse"].name)
		self.assertEqual(settings.sales_item, fixtures["sales_item"].name)

	def test_missing_required_link_raises(self):
		settings = frappe.get_single("Logistic Settings")
		settings.main_warehouse = None
		settings.work_warehouse = None
		settings.sales_item = None

		self.assertRaises(frappe.MandatoryError, settings.save)
