import frappe


def after_install():
    """
    Hook function called after app installation.
    """
    create_item_group()
    create_inventory_dimensions()
    create_accounting_dimensions()
    create_maintenance_fault_types()


def create_item_group():
    """
    Create Item Group record called 'Fuel' if it doesn't exist.
    """
    if not frappe.db.exists("Item Group", "All Item Groups"):
        all_item_groups = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": "All Item Groups",
            "is_group": 1
        })
        all_item_groups.insert(ignore_permissions=True)
        frappe.db.commit()
    
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


def create_accounting_dimensions():
    """
    Create Accounting Dimension records for Truck, Trailer, and Truck Entry.
    Note: This function does not update child tables of Accounting Dimension.
    """
    dimensions = [
        {
            "document_type": "Truck",
            "label": "Truck",
        },
        {
            "document_type": "Trailer",
            "label": "Trailer",
        },
        {
            "document_type": "Truck Entry",
            "label": "Truck Entry",
        }
    ]
    
    for dimension_data in dimensions:
        document_type = dimension_data["document_type"]
        
        # Check if Accounting Dimension already exists for this document type
        if not frappe.db.exists("Accounting Dimension", {"document_type": document_type}):
            try:
                accounting_dimension = frappe.new_doc("Accounting Dimension")
                accounting_dimension.document_type = document_type
                accounting_dimension.label = dimension_data["label"]
                accounting_dimension.disabled = 0
                accounting_dimension.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception as e:
                frappe.logger().error(f"Error creating Accounting Dimension for '{document_type}': {str(e)}")
                frappe.log_error(title=f"Error creating Accounting Dimension for '{document_type}'", message=frappe.get_traceback())
                frappe.db.rollback()


def create_maintenance_fault_types():
    """
    Create default Maintenance Fault Types for trucks and trailers.
    Auto-populates common fault types that require maintenance.
    """

    fault_types = [
        # Engine & Powertrain Faults
        "Engine Overheating",
        "Engine Oil Leak",
        "Engine Misfire",
        "Engine Stalling",
        "Turbocharger Failure",
        "Fuel Injection System Fault",
        "Fuel Pump Failure",
        "Fuel Filter Clogged",
        "Exhaust System Leak",
        "Diesel Particulate Filter (DPF) Blockage",
        "EGR Valve Malfunction",
        "Coolant Leak",
        "Radiator Damage",
        "Water Pump Failure",
        "Alternator Failure",
        "Starter Motor Failure",
        "Battery Failure",
        "Timing Belt/Chain Wear",
        "Transmission Slipping",
        "Transmission Fluid Leak",
        "Clutch Wear",
        "Clutch Slipping",
        "Gearbox Noise",
        "Differential Fault",
        "Driveshaft Vibration",
        "U-Joint Failure",
        "PTO (Power Take-Off) Malfunction",

        # Brake System Faults
        "Brake Pad Wear",
        "Brake Disc/Rotor Wear",
        "Brake Drum Wear",
        "Brake Fluid Leak",
        "Air Brake System Leak",
        "Brake Line Damage",
        "ABS Sensor Fault",
        "ABS Module Failure",
        "Brake Caliper Sticking",
        "Brake Chamber Failure",
        "Slack Adjuster Fault",
        "Parking Brake Malfunction",
        "Brake Booster Failure",
        "Low Brake Air Pressure",

        # Suspension & Steering Faults
        "Shock Absorber Worn",
        "Leaf Spring Crack",
        "Air Suspension Leak",
        "Air Bag Suspension Failure",
        "Steering Fluid Leak",
        "Power Steering Pump Failure",
        "Steering Rack Damage",
        "Steering Column Issue",
        "Tie Rod End Wear",
        "Ball Joint Wear",
        "King Pin Wear",
        "Wheel Bearing Failure",
        "Hub Assembly Damage",
        "Axle Seal Leak",
        "Axle Damage",
        "Fifth Wheel Coupling Wear",
        "Fifth Wheel Lock Mechanism Fault",

        # Tire & Wheel Faults
        "Tire Puncture",
        "Tire Sidewall Damage",
        "Tire Tread Wear",
        "Tire Blowout",
        "Wheel Rim Crack",
        "Wheel Rim Bent",
        "Wheel Nut/Bolt Missing",
        "Wheel Alignment Issue",
        "Tire Pressure Monitoring System Fault",
        "Spare Tire Missing/Damaged",

        # Electrical System Faults
        "Wiring Harness Damage",
        "Fuse Box Failure",
        "ECU/ECM Malfunction",
        "Sensor Failure",
        "Headlight Failure",
        "Tail Light Failure",
        "Brake Light Failure",
        "Turn Signal Failure",
        "Marker Light Failure",
        "Reverse Light Failure",
        "Clearance Light Failure",
        "Interior Light Failure",
        "Horn Malfunction",
        "Electrical Short Circuit",
        "Ground Wire Fault",
        "Trailer Electrical Connector Fault",
        "7-Pin/15-Pin Connector Damage",

        # Body & Structural Faults
        "Cab Corrosion",
        "Body Panel Damage",
        "Chassis Crack",
        "Frame Rail Damage",
        "Cross Member Damage",
        "Door Hinge Worn",
        "Door Lock Malfunction",
        "Window Mechanism Failure",
        "Mirror Damage",
        "Windshield Crack",
        "Windshield Wiper Failure",
        "Washer Fluid System Fault",
        "Step/Ladder Damage",
        "Fuel Tank Damage",
        "Fuel Tank Strap Failure",
        "Mudguard/Fender Damage",
        "Splash Guard Missing",

        # Trailer-Specific Faults
        "Trailer Floor Damage",
        "Trailer Wall Damage",
        "Trailer Roof Leak",
        "Trailer Door Seal Damage",
        "Trailer Door Hinge Failure",
        "Trailer Door Lock Malfunction",
        "Trailer Curtain Tear",
        "Trailer Tarpaulin Damage",
        "Landing Gear Malfunction",
        "Landing Gear Crank Handle Missing",
        "Kingpin Wear",
        "Kingpin Damage",
        "Coupling Device Wear",
        "Dolly Leg Failure",
        "Twist Lock Failure",
        "Container Lock Failure",
        "Refrigeration Unit Failure",
        "Reefer Temperature Control Fault",
        "Reefer Compressor Failure",
        "Insulation Damage (Reefer)",
        "Tanker Valve Leak",
        "Tanker Seal Damage",
        "Bulk Discharge System Fault",

        # Safety Equipment Faults
        "Fire Extinguisher Expired",
        "First Aid Kit Missing",
        "Reflective Triangle Missing",
        "Safety Cone Missing",
        "Wheel Chock Missing",
        "Seat Belt Malfunction",
        "Emergency Exit Blocked",
        "Reverse Alarm Failure",
        "Side Underrun Protection Damage",
        "Rear Underrun Protection Damage",
        "Reflector Missing/Damaged",

        # HVAC & Comfort Faults
        "Air Conditioning Failure",
        "Heater Failure",
        "Blower Motor Failure",
        "HVAC Control Panel Fault",
        "Cabin Air Filter Clogged",
        "AC Refrigerant Leak",
        "Defrost System Failure",

        # Hydraulic System Faults
        "Hydraulic Fluid Leak",
        "Hydraulic Pump Failure",
        "Hydraulic Cylinder Failure",
        "Hydraulic Hose Damage",
        "Hydraulic Valve Malfunction",
        "Tipper/Dump Body Hydraulic Fault",
        "Tail Lift Hydraulic Failure",

        # Air System Faults
        "Air Compressor Failure",
        "Air Dryer Malfunction",
        "Air Tank Leak",
        "Air Line Damage",
        "Air Pressure Regulator Fault",
        "Governor Valve Failure",
        "Check Valve Failure",

        # Telematics & Electronics Faults
        "GPS/Tracking System Failure",
        "Telematics Unit Malfunction",
        "Dashboard Display Fault",
        "Speedometer Malfunction",
        "Tachometer Fault",
        "Odometer Fault",
        "Fuel Gauge Malfunction",
        "Temperature Gauge Fault",
        "Oil Pressure Gauge Fault",
        "Check Engine Light On",
        "Warning Light Malfunction",

        # Miscellaneous Faults
        "Rust/Corrosion",
        "Paint Damage",
        "Decal/Marking Faded",
        "License Plate Light Failure",
        "Registration Plate Holder Damage",
        "Toolbox Lock Failure",
        "Catwalk Damage",
        "Ladder Rung Missing",
        "Grab Handle Loose",
        "Air Horn Failure",
        "CB Radio Malfunction",
        "Camera System Failure",
        "Parking Sensor Fault",
        "Load Securement Equipment Missing",
        "Tarp System Malfunction",
        "Side Door Roller Fault",
        "Rear Door Roller Fault",
    ]

    for fault in fault_types:
        if not frappe.db.exists("Maintenance Fault Type", fault):
            try:
                doc = frappe.get_doc({
                    "doctype": "Maintenance Fault Type",
                    "fault_type": fault
                })
                doc.insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(title=f"Maintenance Fault Type: '{fault}'", message=frappe.get_traceback())

    frappe.db.commit()
