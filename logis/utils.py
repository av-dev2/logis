import frappe
from frappe import _


def create_stock_entry(purpose, items, source_doc):
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
	stock_entry.items = items
	stock_entry.insert(ignore_permissions=True)
	stock_entry.submit()
	
	return stock_entry
