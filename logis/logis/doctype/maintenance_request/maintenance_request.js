// Copyright (c) 2025, AV Dev and contributors
// For license information, please see license.txt

frappe.ui.form.on('Maintenance Request', {
	refresh: function(frm) {
		// Add buttons for actions
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Populate from Template'), function() {
				if (frm.doc.maintenance_template) {
					frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Maintenance Template',
							name: frm.doc.maintenance_template
						},
						callback: function(r) {
							if (r.message) {
								const template = r.message;
								
								// Update problem category and description
								frm.set_value('problem_category', template.problem_category);
								frm.set_value('problem_description', template.description || '');
								
								// Clear and populate inspection steps if template has steps
								if (template.steps && template.steps.length > 0) {
									frm.set_value('no_of_inspections', template.steps.length);
									
									frm.clear_table('inspections');
									template.steps.forEach(function(step, index) {
										frm.add_child('inspections', {
											inspection_no: index + 1,
											inspection_type: 'Visual Inspection',
											description: step.description,
											status: 'Pending'
										});
									});
									frm.refresh_field('inspections');
									frappe.msgprint(__('Template populated with {0} inspections', [template.steps.length]));
								} else {
									frappe.msgprint(__('Template populated successfully'));
								}
							}
						}
					});
				} else {
					frappe.msgprint(__('Please select a Maintenance Template first'));
				}
			}, __('Maintenance'));
		}

		// Show Material Request if created
		if (frm.doc.material_request) {
			frm.add_custom_button(__('View Material Request'), function() {
				frappe.set_route('Form', 'Material Request', frm.doc.material_request);
			}, __('Material Request'));
		}

		// Auto-fill vehicle details when vehicle is selected
		if (frm.doc.vehicle) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: frm.doc.vehicle_type,
					name: frm.doc.vehicle
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('license_plate', r.message.license_plate);
						frm.set_value('make', r.message.make);
						frm.set_value('model', r.message.model);
					}
				}
			});
		}
	},

	vehicle_type: function(frm) {
		// Update vehicle field filter based on vehicle type
		if (frm.doc.vehicle_type === 'Truck') {
			frm.fields_dict.vehicle.get_query = function() {
				return {
					filters: {
						docstatus: 0
					}
				};
			};
		} else if (frm.doc.vehicle_type === 'Trailer') {
			frm.fields_dict.vehicle.get_query = function() {
				return {
					filters: {
						doctype: 'Trailer',
						docstatus: 0
					}
				};
			};
		}
		// Clear vehicle field when type changes
		frm.set_value('vehicle', null);
		frm.set_value('license_plate', '');
		frm.set_value('make', '');
		frm.set_value('model', '');
	},

	vehicle: function(frm) {
		// Auto-fill vehicle details
		if (frm.doc.vehicle) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: frm.doc.vehicle_type,
					name: frm.doc.vehicle
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('license_plate', r.message.license_plate);
						frm.set_value('make', r.message.make);
						frm.set_value('model', r.message.model);
					}
				}
			});
		}
	},

	maintenance_template: function(frm) {
		// Show option to populate from template
		if (frm.doc.maintenance_template) {
			frappe.msgprint(__('Click "Populate from Template" button to auto-fill problem details'));
		}
	},

	no_of_inspections: function(frm) {
		// Auto-create inspection rows
		const current_count = frm.doc.inspections.length;
		const required_count = frm.doc.no_of_inspections;

		if (required_count > current_count) {
			for (let i = current_count; i < required_count; i++) {
				frm.add_child('inspections', {
					inspection_no: i + 1,
					status: 'Pending'
				});
			}
		} else if (required_count < current_count) {
			// Remove extra rows
			for (let i = frm.doc.inspections.length - 1; i >= required_count; i--) {
				frm.get_field('inspections').grid.df.data.splice(i, 1);
			}
		}

		frm.refresh_field('inspections');
	}
});

// Add auto-fetch for item details in spares table
frappe.ui.form.on('Maintenance Spare', {
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Item',
					name: row.item_code
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'item_name', r.message.item_name);
						frappe.model.set_value(cdt, cdn, 'unit_cost', r.message.standard_rate || 0);
						cur_frm.refresh_field('spares');
					}
				}
			});
		}
	},

	quantity_required: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.quantity_required && row.unit_cost) {
			frappe.model.set_value(cdt, cdn, 'total_cost', row.quantity_required * row.unit_cost);
			cur_frm.refresh_field('spares');
		}
	},

	unit_cost: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.quantity_required && row.unit_cost) {
			frappe.model.set_value(cdt, cdn, 'total_cost', row.quantity_required * row.unit_cost);
			cur_frm.refresh_field('spares');
		}
	}
});
