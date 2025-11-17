# Copyright (c) 2025, Administrator and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TripSettlementDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		# TODO: Add type hints for fields here
		pass
	# end: auto-generated types

	def validate(self):
		"""Validate document before saving."""
		pass
	
	def before_save(self):
		"""Called before document is saved."""
		pass
	
	def on_update(self):
		"""Called after document is saved."""
		pass
	
	def on_submit(self):
		"""Called when document is submitted."""
		pass
	
	def on_cancel(self):
		"""Called when document is cancelled."""
		pass
	
	def on_trash(self):
		"""Called before document is deleted."""
		pass
