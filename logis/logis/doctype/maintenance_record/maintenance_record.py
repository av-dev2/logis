# Copyright (c) 2025, elius mgani and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from logis.utils import create_stock_entry


class MaintenanceRecord(Document):
	def before_insert(self):
		"""Actions before inserting the document"""

		self.validate_vehicle()
		self.get_spares()

	def before_save(self):
		"""Actions before saving the document"""

		self.validate_vehicle()
		self.set_remained_qty()

	def before_submit(self):
		"""Actions before document submission"""

		self.create_material_transfer()
		self.create_material_issue()

	def on_submit(self):
		"""Actions on document submission"""

		for row in self.maintenance_requests:
			frappe.db.set_value("Maintenance Request", row.maintenance_request, "status", "Completed")

	def on_cancel(self):
		"""Actions on document cancellation"""

		for row in self.maintenance_requests:
			frappe.db.set_value("Maintenance Request", row.maintenance_request, "status", "In Progress")

	def validate_vehicle(self):
		"""Validate that at least truck or trailer is selected"""

		if not self.truck and not self.trailer:
			frappe.throw("Please select at least a Truck or a Trailer for maintenance record.")

	def set_remained_qty(self):
		"""Calculate remained_qty for each spare and validate qty_used"""

		if not self.spares:
			return

		for row in self.spares:
			qty_provided = row.qty_provided or 0
			qty_used = row.qty_used or 0

			if qty_used > qty_provided:
				frappe.throw(
					f"Row {row.idx}: Qty Used ({qty_used}) cannot be greater than Qty Provided ({qty_provided}) for spare <b>{row.spare}</b>.",
					title="Invalid Quantity",
				)

			row.remained_qty = qty_provided - qty_used

	def get_spares(self):
		"""Get all spare parts from linked maintenance requests"""

		self.spares = []
		self.maintenance_requests = []

		filters = {"posting_date": self.date_requested, "status": "In Progress", "docstatus": 1}

		if self.truck:
			filters["truck"] = self.truck

		if self.trailer:
			filters["trailer"] = self.trailer

		requests = frappe.db.get_all("Maintenance Request", filters=filters)

		for row in requests:
			self.append("maintenance_requests", {"maintenance_request": row.name})

			record_doc = frappe.get_cached_doc("Maintenance Request", row.name)

			for d in record_doc.spares:
				new_spare = self.append("spares")
				new_spare.spare = d.spare
				new_spare.qty_requested = d.qty_requested
				new_spare.qty_provided = d.qty_provided
				new_spare.qty_used = 0
				new_spare.remained_qty = d.remained_qty

	@frappe.whitelist()
	def create_material_transfer(self):
		"""Create Material Transfer for spare parts"""
		if not self.spares or len(self.spares) == 0:
			frappe.throw("No spare parts added to create Material Transfer.")

		# Prepare items for stock entry
		items = []
		settings_doc = frappe.get_cached_doc("Logistic Settings", "Logistic Settings")
		for spare in self.spares:
			if not spare.spare:
				frappe.throw("Spare part item code is required.")

			if spare.remained_qty <= 0:
				continue

			new_item = {
				"item_code": spare.spare,
				"qty": spare.remained_qty,
				"s_warehouse": settings_doc.work_warehouse,
				"t_warehouse": settings_doc.main_warehouse,
			}
			if self.truck:
				new_item["from_truck"] = self.truck

			if self.trailer:
				new_item["from_trailer"] = self.trailer

			items.append(new_item)

		if len(items) == 0:
			return

		stock_entry = create_stock_entry("Material Transfer", items, self)
		self.db_set("material_transfer", stock_entry, update_modified=False)

		return stock_entry

	def create_material_issue(self):
		"""Create Material Issue for spare parts"""
		if not self.spares or len(self.spares) == 0:
			frappe.throw("No spare parts added to create Material Issue.")

		# Prepare items for stock entry
		items = []
		settings_doc = frappe.get_cached_doc("Logistic Settings", "Logistic Settings")
		for spare in self.spares:
			if not spare.spare:
				frappe.throw("Spare part item code is required.")

			if spare.qty_used == 0:
				continue

			new_item = {
				"item_code": spare.spare,
				"qty": spare.qty_used,
				"s_warehouse": settings_doc.work_warehouse,
			}
			if self.truck:
				new_item["from_truck"] = self.truck

			if self.trailer:
				new_item["from_trailer"] = self.trailer

			items.append(new_item)

		if len(items) == 0:
			return

		stock_entry = create_stock_entry("Material Issue", items, self)
		self.db_set("material_issue", stock_entry, update_modified=False)

		return stock_entry
