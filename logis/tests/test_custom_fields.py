"""Feature tests for whitelisted API functions in logis.patches.custom_fields.create_custom_fields.

Covers export_custom_fields(). The DocType-bound whitelisted methods
(Maintenance Request.create_stock_entry, Maintenance Record.create_material_transfer)
are covered in their own doctype test files instead, since they are exercised
as document methods there.
"""

import ast

import frappe
from frappe.tests import IntegrationTestCase

from logis.patches.custom_fields.create_custom_fields import export_custom_fields


class IntegrationTestExportCustomFields(IntegrationTestCase):
	def test_export_known_custom_field(self):
		docname = frappe.db.get_value("Custom Field", {"dt": "Job Card", "fieldname": "truck"})
		if not docname:
			self.skipTest("No 'Job Card.truck' Custom Field found on this site to export")

		result = export_custom_fields(frappe.as_json([docname]))

		exported = ast.literal_eval(result)
		self.assertEqual(len(exported), 1)
		self.assertEqual(exported[0]["fieldname"], "truck")
		self.assertEqual(exported[0]["dt"], "Job Card")

	def test_export_unknown_custom_field_raises(self):
		self.assertRaises(
			frappe.DoesNotExistError, export_custom_fields, frappe.as_json(["Not A Real Custom Field"])
		)

	def test_export_empty_list_returns_empty(self):
		result = export_custom_fields(frappe.as_json([]))

		self.assertEqual(ast.literal_eval(result), [])
