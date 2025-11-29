# Copyright (c) 2025, AV Dev and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.client import get_value


class MaintenanceRequest(Document):
	"""Maintenance Request for Truck/Trailer maintenance tracking"""

	def validate(self):
		"""Validate document before saving"""
		self.validate_vehicle_details()
		self.validate_inspections()
		self.validate_spares()

	def on_submit(self):
		"""Actions on document submission"""
		self.create_material_request()
		self.set_status("Planned")

	def on_cancel(self):
		"""Actions on document cancellation"""
		self.set_status("Cancelled")
		# Cancel linked Material Request if exists
		if self.material_request:
			mr = frappe.get_doc("Material Request", self.material_request)
			if mr.docstatus == 0:
				mr.delete()

	def validate_vehicle_details(self):
		"""Validate and auto-fill vehicle details"""
		if self.vehicle_type and self.vehicle:
			vehicle_doc = frappe.get_doc(self.vehicle_type, self.vehicle)
			self.license_plate = vehicle_doc.license_plate
			self.make = vehicle_doc.make
			self.model = vehicle_doc.model
		elif not self.vehicle:
			frappe.throw("Vehicle is required")

	def validate_inspections(self):
		"""Ensure inspection count matches table entries"""
		if not self.inspections:
			self.inspections = []
		
		# Create inspection rows if count is set but rows are missing
		if self.no_of_inspections > len(self.inspections):
			for i in range(len(self.inspections), self.no_of_inspections):
				self.append("inspections", {
					"inspection_no": i + 1,
					"status": "Pending"
				})

	def validate_spares(self):
		"""Calculate spare costs"""
		if self.spares:
			for spare in self.spares:
				if spare.unit_cost and spare.quantity_required:
					spare.total_cost = spare.quantity_required * spare.unit_cost

	def create_material_request(self):
		"""Create Material Request for spare parts"""
		if not self.spares or len(self.spares) == 0:
			return

		# Create Material Request
		mr = frappe.new_doc("Material Request")
		mr.material_request_type = "Material Transfer"
		mr.purpose = "Material Transfer"
		mr.set_warehouse = frappe.get_value("Logistic Settings", None, "default_store_warehouse") or "Main Store - LOGIS"
		mr.schedule_date = frappe.utils.today()

		for spare in self.spares:
			mr.append("items", {
				"item_code": spare.item_code,
				"item_name": spare.item_name,
				"qty": spare.quantity_required,
				"warehouse": mr.set_warehouse,
				"description": f"Maintenance Request: {self.name}"
			})

		mr.insert(ignore_permissions=True)
		mr.submit()

		self.material_request = mr.name
		self.db_set("material_request", mr.name)

	def set_status(self, status):
		"""Update status"""
		self.status = status
		self.db_set("status", status)

	def on_update_after_submit(self):
		"""Allow updates after submission"""
		pass

	@frappe.whitelist()
	def populate_maintenance_template(self):
		"""Populate inspection steps from maintenance template"""
		if not self.maintenance_template:
			return

		template = frappe.get_doc("Maintenance Template", self.maintenance_template)
		
		# Auto-fill problem category from template
		self.problem_category = template.problem_category
		
		# Populate problem description from template
		if template.description:
			self.problem_description = template.description
