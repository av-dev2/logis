# Copyright (c) 2025, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.utils import get_url_to_form
from logis.utils import create_sales_invoice


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
		self.validate_duplicate_movement_order()

	def validate(self):
		"""Validate document before saving."""
		pass
	
	def before_save(self):
		"""Called before document is saved."""
		pass
	
	def on_update(self):
		"""Called after document is saved."""
		pass

	def before_submit(self):
		self.validate_duplicate_movement_order()
		self.create_invoice()
	
	def create_invoice(self):
		"""Create Sales Invoice for the Trip Settlement."""
		
		if not self.sales_invoice:
			create_sales_invoice(self)
	
	def on_submit(self):
		"""Called when document is submitted."""
		pass
	
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
					& (tsd.parent != self.name)
				)
			).run(as_dict=True)

			if len(duplicates) > 0:
				url = get_url_to_form("Trip Settlement", duplicates[0].parent)
				frappe.throw(
					_(
						"Movement Order: <b>{row.movement_order}</b> RowNo: {row.idx} is already settled in another Trip Settlement: <a href='{url}'><b>{duplicates[0].parent}</b></a>."
					)
				)