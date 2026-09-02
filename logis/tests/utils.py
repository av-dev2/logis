"""Shared fixture helpers for logis test suites.

The test site ships with no master data (no Company, UOM, Warehouse, ...),
so tests that exercise controller logic touching ERPNext stock/accounts need
to create minimal fixtures themselves. All helpers are idempotent.
"""

import frappe


def get_or_create_company(name="Logis Test Company", abbr="LTC"):
	if frappe.db.exists("Company", name):
		company = frappe.get_doc("Company", name)
	else:
		company = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": name,
				"abbr": abbr,
				"default_currency": "USD",
				"country": "United States",
			}
		)
		company.insert(ignore_permissions=True)

	# Several controllers (logis.utils.create_stock_entry, create_expense_journal_entry,
	# ...) fall back to frappe.defaults.get_global_default("company") when the source
	# document has no company of its own. The test site never runs the setup wizard,
	# so nothing else sets this default - without it those controllers fail with
	# MandatoryError: company.
	frappe.defaults.set_global_default("company", company.name)
	return company


def get_or_create_uom(uom_name="Nos"):
	if frappe.db.exists("UOM", uom_name):
		return frappe.get_doc("UOM", uom_name)

	uom = frappe.get_doc({"doctype": "UOM", "uom_name": uom_name})
	uom.insert(ignore_permissions=True)
	return uom


def get_or_create_item_group(name="All Item Groups"):
	if frappe.db.exists("Item Group", name):
		return frappe.get_doc("Item Group", name)

	existing_root = frappe.db.get_all("Item Group", filters={"is_group": 1}, limit=1)
	if existing_root:
		return frappe.get_doc("Item Group", existing_root[0].name)

	group = frappe.get_doc({"doctype": "Item Group", "item_group_name": name, "is_group": 1})
	group.insert(ignore_permissions=True)
	return group


def get_or_create_item(item_code="Test Fuel Item", stock_uom="Nos"):
	if frappe.db.exists("Item", item_code):
		return frappe.get_doc("Item", item_code)

	get_or_create_uom(stock_uom)
	item_group = get_or_create_item_group()

	item = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_code,
			"item_group": item_group.name,
			"stock_uom": stock_uom,
			"is_stock_item": 1,
		}
	)
	item.insert(ignore_permissions=True)
	return item


def get_or_create_warehouse(warehouse_name, company):
	full_name = f"{warehouse_name} - {company.abbr}"
	if frappe.db.exists("Warehouse", full_name):
		return frappe.get_doc("Warehouse", full_name)

	warehouse = frappe.get_doc(
		{
			"doctype": "Warehouse",
			"warehouse_name": warehouse_name,
			"company": company.name,
		}
	)
	warehouse.insert(ignore_permissions=True)
	return warehouse


def receive_opening_stock(testcase, item, warehouse, qty=100, rate=10, company=None, truck=None):
	"""Post a Material Receipt so `item` has a valuation rate and quantity in `warehouse`.

	Needed before any Material Transfer/Issue test, since a bare Item has no
	stock or valuation and ERPNext refuses to move stock it cannot value.
	`testcase` is accepted for call-site symmetry with other fixture helpers.

	Pass `truck` when the stock will later be moved out tagged with that Truck
	inventory dimension (see logis.utils.create_stock_entry) - Truck has
	validate_negative_stock enabled, so a transfer-out under a given truck can
	only draw on stock received into that same dimension.
	"""

	item_row = {
		"item_code": item.name,
		"qty": qty,
		"basic_rate": rate,
		"t_warehouse": warehouse.name,
	}
	if truck:
		item_row["to_truck"] = truck

	stock_entry = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"purpose": "Material Receipt",
			"company": company or frappe.defaults.get_global_default("company"),
			"items": [item_row],
		}
	)
	stock_entry.insert(ignore_permissions=True)
	stock_entry.submit()
	return stock_entry


def get_or_create_customer(customer_name="Test Logis Customer"):
	if frappe.db.exists("Customer", customer_name):
		return frappe.get_doc("Customer", customer_name)

	customer = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": customer_name,
			"customer_type": "Company",
		}
	)
	customer.insert(ignore_permissions=True)
	return customer


def get_or_create_supplier(supplier_name="Test Logis Supplier"):
	if frappe.db.exists("Supplier", supplier_name):
		return frappe.get_doc("Supplier", supplier_name)

	supplier = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": supplier_name,
			"supplier_type": "Company",
		}
	)
	supplier.insert(ignore_permissions=True)
	return supplier


def get_or_create_driver(full_name="Test Logis Driver"):
	existing = frappe.db.get_value("Driver", {"full_name": full_name})
	if existing:
		return frappe.get_doc("Driver", existing)

	driver = frappe.get_doc({"doctype": "Driver", "full_name": full_name})
	driver.insert(ignore_permissions=True)
	return driver


def get_or_create_logistic_settings(main_warehouse, work_warehouse, sales_item):
	settings = frappe.get_single("Logistic Settings")
	settings.main_warehouse = main_warehouse.name
	settings.work_warehouse = work_warehouse.name
	settings.sales_item = sales_item.name
	settings.save(ignore_permissions=True)
	return settings


def get_or_create_truck(license_plate="T 000 TST", make="Scania"):
	if frappe.db.exists("Truck", license_plate):
		return frappe.get_doc("Truck", license_plate)

	truck = frappe.get_doc({"doctype": "Truck", "license_plate": license_plate, "make": make})
	truck.insert(ignore_permissions=True)
	return truck


def get_or_create_trailer(license_plate="TR 000 TST", make="Doepker"):
	if frappe.db.exists("Trailer", license_plate):
		return frappe.get_doc("Trailer", license_plate)

	trailer = frappe.get_doc({"doctype": "Trailer", "license_plate": license_plate, "make": make})
	trailer.insert(ignore_permissions=True)
	return trailer


def setup_stock_fixtures():
	"""Create Company/Warehouses/Item/UOM and wire up Logistic Settings.

	Returns a dict with all created fixtures for use in tests.
	"""

	company = get_or_create_company()
	main_warehouse = get_or_create_warehouse("Main Store", company)
	work_warehouse = get_or_create_warehouse("Work In Progress", company)
	fuel_item = get_or_create_item("Test Fuel")
	spare_item = get_or_create_item("Test Spare Part")
	sales_item = get_or_create_item("Test Transport Service")
	get_or_create_logistic_settings(main_warehouse, work_warehouse, sales_item)

	return {
		"company": company,
		"main_warehouse": main_warehouse,
		"work_warehouse": work_warehouse,
		"fuel_item": fuel_item,
		"spare_item": spare_item,
		"sales_item": sales_item,
	}
