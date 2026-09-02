# Copyright (c) 2025, elius mgani and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from logis.tests.utils import setup_stock_fixtures

# See test_logistic_settings.py: the test site has no `payments` app, so the
# automatic test-record dependency walker crashes if allowed to recurse into
# Account -> ... -> Payment Gateway. We supply our own fixtures instead.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Account"]


class IntegrationTestLogisticExpense(IntegrationTestCase):
	def setUp(self):
		self.fixtures = setup_stock_fixtures()
		self.expense_account = frappe.db.get_value(
			"Account",
			{"company": self.fixtures["company"].name, "is_group": 0, "root_type": "Expense"},
		)
		if not self.expense_account:
			parent = frappe.db.get_value(
				"Account",
				{"company": self.fixtures["company"].name, "root_type": "Expense", "is_group": 1},
			)
			account = frappe.get_doc(
				{
					"doctype": "Account",
					"account_name": "Test Logistics Expense",
					"company": self.fixtures["company"].name,
					"parent_account": parent,
					"account_type": "Expense Account",
				}
			)
			account.insert(ignore_permissions=True)
			self.expense_account = account.name

	def test_creation(self):
		doc = frappe.get_doc(
			{
				"doctype": "Logistic Expense",
				"expense_name": "Toll Fee",
				"fixed_amount": 25.5,
				"expense_account": self.expense_account,
			}
		)
		doc.insert()

		self.assertEqual(doc.name, "Toll Fee")
		self.assertEqual(doc.fixed_amount, 25.5)

	def test_missing_required_fields_raises(self):
		doc = frappe.get_doc({"doctype": "Logistic Expense", "expense_name": "Parking Fee"})

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_duplicate_expense_name_not_allowed(self):
		frappe.get_doc(
			{
				"doctype": "Logistic Expense",
				"expense_name": "Weighbridge Fee",
				"fixed_amount": 10,
				"expense_account": self.expense_account,
			}
		).insert()

		duplicate = frappe.get_doc(
			{
				"doctype": "Logistic Expense",
				"expense_name": "Weighbridge Fee",
				"fixed_amount": 10,
				"expense_account": self.expense_account,
			}
		)
		self.assertRaises(frappe.DuplicateEntryError, duplicate.insert)
