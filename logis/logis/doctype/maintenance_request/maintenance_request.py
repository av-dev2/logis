# Copyright (c) 2025, AV Dev and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from logis.utils import create_stock_entry as create_material_transfer


class MaintenanceRequest(Document):
	"""Maintenance Request for Truck/Trailer maintenance tracking"""

	def before_save(self):
		"""Actions before saving the document"""

		self.set_status("Pending")
		self.validate_duplicate_spares()

	def validate_duplicate_spares(self):
		"""Validate that there are no duplicate spare parts in the spares child table.
		If duplicates are found, throw an error suggesting to merge quantities."""

		if not self.spares:
			return

		spare_counts = {}
		for row in self.spares:
			if not row.spare:
				continue

			if row.spare in spare_counts:
				spare_counts[row.spare]["count"] += 1
				spare_counts[row.spare]["total_qty"] += row.qty_requested or 0
			else:
				spare_counts[row.spare] = {"count": 1, "total_qty": row.qty_requested or 0}

		# Find duplicates
		duplicates = {spare: info for spare, info in spare_counts.items() if info["count"] > 1}

		if duplicates:
			duplicate_messages = []
			for spare, info in duplicates.items():
				duplicate_messages.append(
					f"<b>{spare}</b> appears {info['count']} times. "
					f"Please merge into one row with total quantity: {info['total_qty']}"
				)

			frappe.throw(
				"Duplicate spare parts found in the Spares table:<br><br>"
				+ "<br>".join(duplicate_messages)
				+ "<br><br>Please remove duplicates and merge the quantities into a single row.",
				title="Duplicate Spares Not Allowed",
			)

	def before_submit(self):
		"""Actions before document submission"""

		self.validate_vehicle()
		self.validate_spare_required()
		self.validate_spare_request()

	def on_submit(self):
		"""Actions on document submission"""

		self.set_status("In Progress")

	def on_cancel(self):
		"""Actions on document cancellation"""

		self.set_status("Cancelled")

	def set_status(self, status):
		"""Update status"""

		self.status = status
		self.db_set("status", status)

	def validate_vehicle(self):
		"""Validate that at least truck or trailer is selected"""

		if not self.truck and not self.trailer:
			frappe.throw("Please select at least a Truck or a Trailer for maintenance request.")

	@frappe.whitelist()
	def create_stock_entry(self):
		"""Create Material Request for spare parts"""
		if not self.spares or len(self.spares) == 0:
			frappe.throw("No spare parts added to create Stock Entry.")

		# Prepare items for stock entry
		items = []
		settings_doc = frappe.get_cached_doc("Logistic Settings", "Logistic Settings")
		for spare in self.spares:
			if not spare.spare:
				frappe.throw("Spare part item code is required.")

			if spare.qty_requested <= 0:
				frappe.throw(f"Quantity for spare part {spare.spare} must be greater than 0.")

			new_row = {
				"item_code": spare.spare,
				"qty": spare.qty_requested,
				"s_warehouse": settings_doc.main_warehouse,
				"t_warehouse": settings_doc.work_warehouse,
			}

			if self.truck:
				new_row["to_truck"] = self.truck

			if self.trailer:
				new_row["to_trailer"] = self.trailer

			items.append(new_row)

		# Create Stock Entry
		stock_entry = create_material_transfer("Material Transfer", items, self, submit=False)

		self.db_set("stock_entry", stock_entry, update_modified=False)

		return stock_entry

	def validate_spare_required(self):
		"""Validate spare parts details"""

		if self.no_spare_required == 1:
			self.spares = []
			return

		if len(self.spares) == 0:
			frappe.throw("Please add at least one spare part or select 'No Spare Required'.")

	def validate_spare_request(self):
		"""Validate that at least one spare part is requested"""

		if not self.stock_entry:
			return

		stock_entry_doc = frappe.get_doc("Stock Entry", self.stock_entry)
		if stock_entry_doc.docstatus != 1:
			frappe.throw("The requested spare parts have not been approved. Please inform the store manager.")
