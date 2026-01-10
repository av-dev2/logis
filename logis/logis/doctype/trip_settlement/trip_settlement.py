# Copyright (c) 2025, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.utils import get_url_to_form
from logis.utils import create_sales_invoice, create_stock_entry


class TripSettlement(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		# TODO: Add type hints for fields here
		pass
	# end: auto-generated types

	def before_insert(self):
		"""Called before inserting a new document."""
		pass

	def validate(self):
		"""Validate document before saving."""
		pass
	
	def before_save(self):
		self.validate_duplicate_movement_order()
		self.set_total_fuel_provided()
		self.set_total_income()
	
	def on_update(self):
		"""Called after document is saved."""
		pass

	def before_submit(self):
		self.validate_duplicate_movement_order()
		self.create_stock_entry()
		self.create_invoice()
	
	def create_invoice(self):
		"""Create Sales Invoice for the Trip Settlement."""
		
		if not self.sales_invoice:
			create_sales_invoice(self)
	
	def on_submit(self):
		"""Called when document is submitted."""
		frappe.db.set_value(
			"Trip Assignment",
			self.trip_assignment,
			"settled",
			1
		)
	
	def on_cancel(self):
		"""Called when document is cancelled."""
		pass
	
	def on_trash(self):
		"""Called before document is deleted."""
		pass
	
	def validate_duplicate_movement_order(self):
		"""Validate that there are no duplicate movement orders in the settlement."""

		tsd = DocType("Trip Settlement Detail")

		for row in self.trips:
			duplicates = (
				frappe.qb.from_(tsd)
				.select(
					tsd.name,
					tsd.parent
				)
				.where(
					(tsd.movement_order == row.movement_order)
					& (tsd.name != row.name)
				)
			).run(as_dict=True)

			if len(duplicates) > 0:
				url = get_url_to_form("Trip Settlement", duplicates[0].parent)
				frappe.throw(
					_(
						f"Movement Order: <b>{row.movement_order}</b> RowNo: {row.idx} is already settled in another Trip Settlement: <a href='{url}'><b>{duplicates[0].parent}</b></a>."
					)
				)
	
	def set_total_fuel_provided(self):
		"""Set the total fuel provided for the trip settlement."""
		self.no_of_trips = len(self.trips)
		self.fuel_consumed = self.no_of_trips * self.fuel_per_each_trip
		self.fuel_remained = self.fuel_provided - self.fuel_consumed
	
	def set_total_income(self):
		"""Set the total income for the trip settlement."""
		total = 0
		for row in self.trips:
			total += row.amount
		
		self.total_income = total
	
	def create_stock_entry(self):
		"""
		Create Stock Entry for fuel material transfer from Store to Work in Progress.
		"""
		
		# Prepare items for stock entry
		trip_assignment = frappe.get_cached_doc("Trip Assignment", self.trip_assignment)
		settings_doc = frappe.get_cached_doc("Logistic Settings", "Logistic Settings")
		items = [{
			"item_code": trip_assignment.fuel_type,
			"qty": self.fuel_consumed,
			"s_warehouse": settings_doc.work_warehouse,
			"from_truck": self.truck,
			"from_trailer": self.trailer,
			"from_truck_entry": self.truck_entry
		}]
		
		stock_entry = create_stock_entry(
			purpose="Material Issue",
			items=items,
			source_doc=self
		)
		
		self.db_set("stock_entry", stock_entry, update_modified=False)
	