import frappe


def after_install():
    """
    Hook function called after app installation.
    """
    create_item_group()


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
        frappe.logger().info("Item Group 'Fuel' created successfully")
    else:
        frappe.logger().info("Item Group 'Fuel' already exists")
