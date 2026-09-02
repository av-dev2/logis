import frappe
from frappe import _
from frappe.utils import nowdate


def create_stock_entry(purpose, items, source_doc, submit=True):
	"""
	Create a Stock Entry for Material Transfer or Material Issue with Inventory Dimensions.

	Args:
		purpose (str): Stock Entry purpose - "Material Transfer" or "Material Issue"
		items (list): List of dictionaries containing item details with keys:
			- item_code: Item code
			- qty: Quantity to transfer/issue
			- s_warehouse: Source warehouse (required for Material Transfer)
			- t_warehouse: Target warehouse (required for Material Transfer and Material Issue)
			- truck: Truck dimension (optional)
			- trailer: Trailer dimension (optional)
			- truck_entry: Truck Entry dimension (optional)
		source_doc (Document): Source document reference

	Returns:
		Document: Created Stock Entry document
	"""

	if not purpose or purpose not in ["Material Transfer", "Material Issue"]:
		frappe.throw(_("Purpose must be either 'Material Transfer' or 'Material Issue'"))

	if not items or not isinstance(items, list):
		frappe.throw(_("Items must be provided as a list"))

	# Create Stock Entry document
	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.stock_entry_type = purpose
	stock_entry.purpose = purpose
	stock_entry.company = source_doc.get("company") or frappe.defaults.get_global_default("company")
	# stock_entry.items = items
	for itm in items:
		item_row = stock_entry.append("items")
		item_row.item_code = itm.get("item_code")
		item_row.qty = itm.get("qty")
		item_row.s_warehouse = itm.get("s_warehouse")

		if purpose == "Material Transfer":
			item_row.t_warehouse = itm.get("t_warehouse")

			# Set accounting dimensions
			if itm.get("from_truck"):
				item_row.truck = itm.get("from_truck")

			if itm.get("from_trailer"):
				item_row.trailer = itm.get("from_trailer")

			if itm.get("from_truck_entry"):
				item_row.truck_entry = itm.get("from_truck_entry")

			if itm.get("to_truck"):
				item_row.to_truck = itm.get("to_truck")

			if itm.get("to_trailer"):
				item_row.to_trailer = itm.get("to_trailer")

			if itm.get("to_truck_entry"):
				item_row.to_truck_entry = itm.get("to_truck_entry")

		if purpose == "Material Issue":
			if itm.get("from_truck"):
				item_row.truck = itm.get("from_truck")

			if itm.get("from_trailer"):
				item_row.trailer = itm.get("from_trailer")

			if itm.get("from_truck_entry"):
				item_row.truck_entry = itm.get("from_truck_entry")

			if itm.get("to_truck"):
				item_row.to_truck = itm.get("to_truck")

			if itm.get("to_trailer"):
				item_row.to_trailer = itm.get("to_trailer")

			if itm.get("to_truck_entry"):
				item_row.to_truck_entry = itm.get("to_truck_entry")

	stock_entry.save(ignore_permissions=True)
	if submit:
		stock_entry.submit()

	frappe.msgprint(_(f"Stock Entry: <b>{stock_entry.name}</b> created successfully"), alert=True)

	return stock_entry.name


def create_expense_journal_entry(source_doc):
	"""
	Create a Journal Entry for expenses listed in Trip Assignment.

	Args:
		source_doc (Document): Trip Assignment document

	Returns:
		Document: Created Journal Entry document or None if no expenses
	"""

	if not source_doc.expenses or len(source_doc.expenses) == 0:
		return None

	# Get company defaults
	company = source_doc.company or frappe.defaults.get_global_default("company")

	# Fetch default cash account from company
	company_doc = frappe.get_cached_doc("Company", company)
	default_cash_account = company_doc.default_cash_account

	if not default_cash_account:
		frappe.throw(_(f"Default Cash Account is not set for Company {company}"))

	# Prepare journal entry accounts
	accounts = []
	total_debit = 0

	# Add debit entries for each expense
	for expense in source_doc.expenses:
		if not expense.expense_account:
			frappe.throw(_(f"Expense Account is required for expense {expense.expense_name}"))

		if expense.amount <= 0:
			frappe.throw(_(f"Expense amount must be greater than 0 for expense {expense.expense_name}"))

		debit_row = {
			"account": expense.expense_account,
			"debit_in_account_currency": expense.amount,
			"credit_in_account_currency": 0,
			# Add accounting dimensions
			"truck": source_doc.truck,
			"trailer": source_doc.trailer,
			"truck_entry": source_doc.truck_entry,
		}
		accounts.append(debit_row)
		total_debit += expense.amount

	# Add credit entry for default cash account
	if total_debit > 0:
		credit_row = {
			"account": default_cash_account,
			"debit_in_account_currency": 0,
			"credit_in_account_currency": total_debit,
			# Add accounting dimensions
			"truck": source_doc.truck,
			"trailer": source_doc.trailer,
			"truck_entry": source_doc.truck_entry,
		}
		accounts.append(credit_row)

	if not accounts or total_debit == 0:
		frappe.throw(_("No valid expense entries found to create Journal Entry"))

	# Prepare remarks
	remarks = _(f"Trip Assignment: <b>{source_doc.name}</b>")

	# Create Journal Entry
	journal_entry = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"posting_date": source_doc.posting_date or nowdate(),
			"company": company,
			"accounts": accounts,
			"user_remark": remarks,
			# "cheque_no": source_doc.name,
			# "cheque_date": source_doc.posting_date
		}
	)

	journal_entry.flags.ignore_permissions = True
	frappe.flags.ignore_account_permission = True
	journal_entry.insert()
	# journal_entry.submit()

	frappe.msgprint(_(f"Journal Entry: <b>{journal_entry.name}</b> created successfully"), alert=True)

	return journal_entry.name


def create_vehicle(source_doc):
	"""
	Create a Vehicle document from Truck or Trailer doctype.

	This function is called from after_insert event of Truck and Trailer doctypes
	to automatically create a corresponding Vehicle record.

	Args:
		source_doc (Document): Truck or Trailer document

	Returns:
		str: Name of the created Vehicle document or None if already exists
	"""

	# Determine doctype and set appropriate flags

	if source_doc.doctype not in ["Truck", "Trailer"]:
		frappe.throw(_("create_vehicle function can only be called from Truck or Trailer doctype"))

	# Check if Vehicle already exists with this license plate
	if frappe.db.exists("Vehicle", source_doc.license_plate):
		frappe.msgprint(_(f"Vehicle <b>{source_doc.license_plate}</b> already exists"), alert=True)
		return None

	# Prepare Vehicle data from source document
	vehicle_data = {
		"doctype": "Vehicle",
		"license_plate": source_doc.license_plate,
		"make": source_doc.make,
		"model": source_doc.model,
		"chassis_no": source_doc.chassis_no,
		"csf_tz_engine_number": source_doc.engine_no,
		"color": source_doc.color,
		"wheels": source_doc.wheels,
		"doors": source_doc.doors,
		"disabled": source_doc.disabled or 0,
		"is_truck": 1 if source_doc.doctype == "Truck" else 0,
		"is_trailer": 1 if source_doc.doctype == "Trailer" else 0,
	}

	vehicle = frappe.get_doc(vehicle_data)
	vehicle.flags.ignore_mandatory = True
	vehicle.flags.ignore_permissions = True
	vehicle.insert()

	frappe.msgprint(
		_(f"Vehicle <b>{vehicle.name}</b> created successfully from {source_doc.doctype}"), alert=True
	)

	return vehicle.name


def create_sales_invoice(source_doc):
	"""
	Create a Sales Invoice from Trip Settlement document.

	This function is called from the before_submit event of Trip Settlement doctype.
	It picks the sales item from Logistic Settings and uses the total_income from
	Trip Settlement as the rate and amount.

	Args:
		source_doc (Document): Trip Settlement document

	Returns:
		str: Name of the created Sales Invoice document
	"""

	# Validate total_income
	if not source_doc.total_income or source_doc.total_income <= 0:
		frappe.throw(_("Total Income must be greater than 0 to create Sales Invoice"))

	# Get sales item from Logistic Settings
	logistic_settings = frappe.get_single("Logistic Settings")

	if not logistic_settings.sales_item:
		frappe.throw(_("Sales Item is not configured in Logistic Settings. Please configure it first."))

	item = frappe.get_cached_doc("Item", logistic_settings.sales_item)

	# Prepare Sales Invoice Item
	items = [
		{
			"item_code": item.name,
			"item_name": item.item_name,
			"description": item.description or item.item_name,
			"qty": 1,
			"uom": item.stock_uom,
			"rate": source_doc.total_income,
			"amount": source_doc.total_income,
			"truck": source_doc.truck,
			"trailer": source_doc.trailer,
			"truck_entry": source_doc.truck_entry,
		}
	]

	# Create Sales Invoice
	sales_invoice = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"customer": source_doc.customer,
			"company": source_doc.company,
			"posting_date": source_doc.posting_date or nowdate(),
			"items": items,
			"truck": source_doc.truck,
			"trailer": source_doc.trailer,
			"truck_entry": source_doc.truck_entry,
			"remarks": _(f"Sales Invoice for Trip Settlement: {source_doc.name}"),
		}
	)

	sales_invoice.flags.ignore_permissions = True
	sales_invoice.insert()
	sales_invoice.submit()

	# Update Trip Settlement with Sales Invoice reference
	frappe.db.set_value("Trip Settlement", source_doc.name, "sales_invoice", sales_invoice.name)

	frappe.msgprint(_(f"Sales Invoice: <b>{sales_invoice.name}</b> created successfully"), alert=True)

	return sales_invoice.name


def create_purchase_invoice(source_doc):
	"""
	Create Purchase Invoices from Trip Assignment document.

	This function is called from the before_submit event of Trip Assignment doctype.
	It creates multiple Purchase Invoices based on unique suppliers in the expenses child table.
	Each unique supplier gets one Purchase Invoice with all their expense items.
	All Purchase Invoices are marked as paid with Cash mode of payment.

	Args:
		source_doc (Document): Trip Assignment document

	Returns:
		list: List of names of created Purchase Invoice documents or None if no expenses
	"""

	# Check if there are expenses
	if not source_doc.expenses or len(source_doc.expenses) == 0:
		return None

	# Get company
	company = source_doc.company or frappe.defaults.get_global_default("company")

	# Get default cash account from company
	company_doc = frappe.get_cached_doc("Company", company)
	default_cash_account = company_doc.default_cash_account

	if not default_cash_account:
		frappe.throw(_(f"Default Cash Account is not set for Company {company}"))

	# Group expenses by supplier
	supplier_expenses = {}
	for expense in source_doc.expenses:
		if not expense.supplier:
			frappe.throw(_(f"Supplier is required for expense {expense.expense_name}"))

		if not expense.expense_name:
			frappe.throw(_("Expense Name is required for all expenses"))

		if not expense.amount or expense.amount <= 0:
			frappe.throw(_(f"Expense amount must be greater than 0 for expense {expense.expense_name}"))

		if expense.supplier not in supplier_expenses:
			supplier_expenses[expense.supplier] = []

		supplier_expenses[expense.supplier].append(expense)

	if not supplier_expenses:
		frappe.throw(_("No valid expense items found to create Purchase Invoice"))

	created_invoices = []

	# Create Purchase Invoice for each supplier
	for supplier, expenses in supplier_expenses.items():
		# Prepare Purchase Invoice Items for this supplier
		items = []
		total_amount = 0

		for expense in expenses:
			# Get item details
			item = frappe.get_cached_doc("Item", expense.expense_name)

			expense_account = frappe.get_value(
				"Item Default", {"parent": item.name, "company": company}, "expense_account"
			)

			if not expense_account:
				frappe.throw(_(f"Expense Account is required for expense {expense.expense_name}"))

			item_row = {
				"item_code": expense.expense_name,
				"item_name": item.item_name,
				"description": item.description or item.item_name,
				"qty": 1,
				"uom": item.stock_uom or item.purchase_uom or "Nos",
				"rate": expense.amount,
				"amount": expense.amount,
				"expense_account": expense_account,
				# Add accounting dimensions
				"truck": source_doc.truck,
				"trailer": source_doc.trailer,
				"truck_entry": source_doc.truck_entry,
			}
			items.append(item_row)
			total_amount += expense.amount

		# Create Purchase Invoice
		purchase_invoice = frappe.get_doc(
			{
				"doctype": "Purchase Invoice",
				"supplier": supplier,
				"company": company,
				"posting_date": source_doc.posting_date or nowdate(),
				"bill_date": source_doc.posting_date or nowdate(),
				"items": items,
				"truck": source_doc.truck,
				"trailer": source_doc.trailer,
				"truck_entry": source_doc.truck_entry,
				"remarks": _(f"Purchase Invoice for Trip Assignment: {source_doc.name}"),
				"is_paid": 1,
				"mode_of_payment": "Cash",
				"cash_bank_account": default_cash_account,
				"paid_amount": total_amount,
			}
		)

		purchase_invoice.flags.ignore_permissions = True
		frappe.flags.ignore_account_permission = True
		purchase_invoice.insert()
		purchase_invoice.submit()

		created_invoices.append(purchase_invoice.name)
		frappe.msgprint(
			_(f"Purchase Invoice: <b>{purchase_invoice.name}</b> created for supplier <b>{supplier}</b>"),
			alert=True,
		)

	return created_invoices


def update_maintenance_request_qty_provided(doc, method):
	"""
	Update qty_provided in Maintenance Request child table based on Stock Entry submission.

	Called from Stock Entry on_submit event for Material Transfer purpose.
	Finds the Maintenance Request that references this Stock Entry and updates
	the qty_provided field in the 'Maintenance Spare Detail' child table.

	Args:
		doc (Document): Stock Entry document
		method (str): Event method name (on_submit)
	"""

	# Only process Material Transfer stock entries
	if doc.purpose != "Material Transfer":
		return

	# Find Maintenance Request that references this Stock Entry
	maintenance_request = frappe.db.get_value(
		"Maintenance Request", {"stock_entry": doc.name, "docstatus": ["!=", 2]}, "name"
	)

	if not maintenance_request:
		# No Maintenance Request found referencing this Stock Entry, do nothing
		return

	# Get Maintenance Request document
	mr_doc = frappe.get_doc("Maintenance Request", maintenance_request)

	# Build a dictionary of items and quantities from Stock Entry
	stock_entry_items = {}
	for item in doc.items:
		item_code = item.item_code
		qty = item.qty or 0

		if item_code in stock_entry_items:
			stock_entry_items[item_code] += qty
		else:
			stock_entry_items[item_code] = qty

	# Update qty_provided in the spares child table
	for spare in mr_doc.spares:
		if spare.spare in stock_entry_items:
			# Update qty_provided with the quantity from Stock Entry
			frappe.db.set_value(
				"Maintenance Spare Detail", spare.name, "qty_provided", stock_entry_items[spare.spare]
			)
