# Copyright (c) 2025, elius mgani and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TripAssignment(Document):
	def before_submit(self):
		self.create_truck_entry()

	def create_truck_entry(self):
		truck_entry = f"{self.truck}/{self.trailer}"

		if not frappe.db.exists("Truck Entry", truck_entry):
			truck_entry_doc = frappe.new_doc("Truck Entry")
			truck_entry_doc.truck_name = truck_entry
			truck_entry_doc.save(ignore_permissions=True)

			self.truck_name = truck_entry_doc.name
		
		else:
			self.truck_name = truck_entry
