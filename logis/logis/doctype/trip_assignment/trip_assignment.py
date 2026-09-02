# Copyright (c) 2025, elius mgani and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from logis.utils import create_expense_journal_entry, create_purchase_invoice, create_stock_entry


class TripAssignment(Document):
	def before_save(self):
		self.set_total_fuel()
		self.fetch_pfuel_values()
		self.set_total_expense()

	def before_submit(self):
		self.create_truck_entry()
		self.create_fuel_stock_entry()
		self.create_expense_purchase_invoice()
		# self.create_expense_journal_entry()

	def set_total_fuel(self):
		requested_fuel = ((self.fuel_per_trip or 0) * (self.expected_trips or 0)) - (
			self.previous_remained_fuel or 0
		)

		self.todays_requested_fuel = requested_fuel
		self.total_fuel = (
			(self.previous_remained_fuel or 0) + (self.todays_requested_fuel or 0) + (self.reserve_fuel or 0)
		)

	def set_total_expense(self):
		total = 0
		if self.expenses:
			for expense in self.expenses:
				total += expense.amount

		self.total_expense = total

	def fetch_pfuel_values(self):
		"""
		Fetch previous issued fuel and remained fuel from the latest submitted Trip Settlement
		for the same truck.
		"""
		if not self.truck:
			return

		# Get the latest submitted Trip Settlement for this truck
		latest_settlement = frappe.db.get_value(
			"Trip Settlement",
			filters={
				"truck": self.truck,
				"docstatus": 1,  # Only submitted documents
			},
			fieldname=["fuel_provided", "fuel_remained"],
			order_by="posting_date desc, creation desc",
		)

		if latest_settlement:
			# latest_settlement returns a tuple (fuel_provided, fuel_remained)
			self.previous_issued_fuel = latest_settlement[0] or 0
			self.previous_remained_fuel = latest_settlement[1] or 0

	def create_truck_entry(self):
		truck_entry = f"{self.truck}/{self.trailer}"

		if not frappe.db.exists("Truck Entry", truck_entry):
			truck_entry_doc = frappe.new_doc("Truck Entry")
			truck_entry_doc.truck_name = truck_entry
			truck_entry_doc.save(ignore_permissions=True)

			self.truck_entry = truck_entry_doc.name

		else:
			self.truck_entry = truck_entry

	def create_fuel_stock_entry(self):
		"""
		Create Stock Entry for fuel material transfer from Store to Work in Progress.
		"""
		if not self.fuel_type or not self.total_fuel:
			frappe.throw(_("Fuel Type and Requested Fuel are required to create stock entry"))

		if self.total_fuel <= 0:
			frappe.throw(_("Requested Fuel must be greater than 0"))

		# Prepare items for stock entry
		settings_doc = frappe.get_cached_doc("Logistic Settings", "Logistic Settings")
		items = [
			{
				"item_code": self.fuel_type,
				"qty": self.total_fuel,
				"s_warehouse": settings_doc.main_warehouse,
				"t_warehouse": settings_doc.work_warehouse,
				"to_truck": self.truck,
				"to_trailer": self.trailer,
				"to_truck_entry": self.truck_entry,
			}
		]

		stock_entry = create_stock_entry(purpose="Material Transfer", items=items, source_doc=self)

		self.db_set("stock_entry", stock_entry, update_modified=False)

	def create_expense_purchase_invoice(self):
		"""
		Create Purchase Invoice for expenses listed in Trip Assignment.
		"""
		if not self.expenses or len(self.expenses) == 0:
			frappe.throw(_("No expenses found to create Purchase Invoice"))

		purchase_invoice = create_purchase_invoice(source_doc=self)

		self.db_set("purchase_invoice", ", ".join(purchase_invoice), update_modified=False)

	def create_expense_journal_entry(self):
		"""
		Create Journal Entry for expenses listed in Trip Assignment.
		"""
		if not self.expenses or len(self.expenses) == 0:
			frappe.throw(_("No expenses found to create Journal Entry"))

		journal_entry = create_expense_journal_entry(source_doc=self)

		self.db_set("journal_entry", journal_entry, update_modified=False)
