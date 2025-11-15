# Copyright (c) 2025, elius mgani and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from logis.utils import create_stock_entry


class TripAssignment(Document):
	def before_submit(self):
		self.create_truck_entry()
		self.create_fuel_stock_entry()


	def create_truck_entry(self):
		truck_entry = f"{self.truck}/{self.trailer}"

		if not frappe.db.exists("Truck Entry", truck_entry):
			truck_entry_doc = frappe.new_doc("Truck Entry")
			truck_entry_doc.truck_name = truck_entry
			truck_entry_doc.save(ignore_permissions=True)

			self.truck_name = truck_entry_doc.name
		
		else:
			self.truck_name = truck_entry
	

	def create_fuel_stock_entry(self):
		"""
		Create Stock Entry for fuel material transfer from Store to Work in Progress.
		"""
		if not self.fuel_type or not self.requested_fuel:
			frappe.throw(_("Fuel Type and Requested Fuel are required to create stock entry"))
		
		if self.requested_fuel <= 0:
			frappe.throw(_("Requested Fuel must be greater than 0"))
		
		# Prepare items for stock entry
		items = [{
			"item_code": self.fuel_type,
			"qty": self.requested_fuel,
			"s_warehouse": frappe.db.get_value(
				"Warehouse",
				{"name": ["like", f"%Store%"]},
				"name"
			),
			"t_warehouse": frappe.db.get_value(
				"Warehouse",
				{"name": ["like", f"%Work In Progress%"]},
				"name"
			),
			"truck": self.truck,
			"trailer": self.trailer,
			"truck_entry": self.truck_entry
		}]
		
		stock_entry = create_stock_entry(
			purpose="Material Transfer",
			items=items,
			source_doc=self
		)
		
		self.db_set("stock_entry", stock_entry.name, update_modified=False)
