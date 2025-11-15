import frappe


def after_install():
    """
    Hook function called after app installation.
    """
    create_item_group()
    create_inventory_dimensions()


def create_item_group():
    """
    Create Item Group record called 'Fuel' if it doesn't exist.
    """
    if not frappe.db.exists("Item Group", "Fuel"):
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": "Fuel",
            "parent_item_group": "All Item Groups",
            "is_group": 0
        })
        item_group.insert(ignore_permissions=True)
        frappe.db.commit()


def create_inventory_dimensions():
    """
    Create Inventory Dimension records for Truck, Trailer, and Truck Entry.
    """
    dimensions = [
        {
            "dimension_name": "Truck",
            "reference_document": "Truck",
        },
        {
            "dimension_name": "Trailer",
            "reference_document": "Trailer",
        },
        {
            "dimension_name": "Truck Entry",
            "reference_document": "Truck Entry",
        }
    ]
    
    for dimension_data in dimensions:
        dimension_name = dimension_data["dimension_name"]
        
        if not frappe.db.exists("Inventory Dimension", dimension_name):
            try:
                inventory_dimension = frappe.new_doc("Inventory Dimension")
                inventory_dimension.dimension_name = dimension_name
                inventory_dimension.reference_document = dimension_data["reference_document"]
                inventory_dimension.apply_to_all_doctypes = 1
                inventory_dimension.validate_negative_stock = 1
                inventory_dimension.disabled = 0
                inventory_dimension.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception as e:
                frappe.logger().error(f"Error creating Inventory Dimension '{dimension_name}': {str(e)}")
                frappe.log_error(title=f"Error creating Inventory Dimension '{dimension_name}'", message=frappe.get_traceback())
                frappe.db.rollback()
