// Copyright (c) 2025, AV Dev and contributors
// For license information, please see license.txt

frappe.ui.form.on('Maintenance Request', {
	setup: (frm) => {
		frm.trigger('set_query');
		frm.trigger('validate_add_spare');
	},

	refresh: (frm) => {
		frm.trigger('set_query');
		frm.trigger('validate_add_spare');

		// Show Stock Entry if created
		if (frm.doc.stock_entry) {
			frm.add_custom_button(__('View Stock Entry'), function() {
				frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
			}, __('View'));
		}
	},

	onload: (frm) => {
		frm.trigger('set_query');
		frm.trigger('validate_add_spare');
	},
	
	request_spares: (frm) => {
		if (frm.doc.spares.length === 0) {
			frappe.msgprint(__('Please add at least one spare part to request.'));
			return;
		}

		if (frm.is_dirty()) {
			frm.save().then(() => {
				frm.reload_doc();
			});
		}

		frappe.call({
			method: 'create_stock_entry',
			doc: frm.doc,
			freeze: true,
			freeze_message: __('Creating Stock Entry...'),
			callback: (r) => {
				if (r.message) {
					frm.reload_doc();
					frappe.msgprint(__('Stock Entry {0} created successfully.', [r.message]));
				} else {
					frappe.msgprint(__('No spare parts were requested.'));
				}
			}
		});
	},
	set_query: (frm) => {
		frm.set_query('spare', 'spares', () => {
			return {
				filters: {
					is_stock_item: 1
				}
			};
		});
	},
	validate_add_spare: (frm) => {
		if (frm.doc.stock_entry) {
			frm.get_field("spares").grid.cannot_add_rows = true;

			$("*[data-fieldname='spares']").find(".grid-remove-rows").hide();
			$("*[data-fieldname='spares']").find(".grid-remove-all-rows").hide();
		}
	},
});

// Add auto-fetch for item details in spares table
frappe.ui.form.on('Maintenance Spare Detail', {
	form_render: (frm, cdt, cdn) => {
		if (frm.doc.stock_entry) {
			frm.fields_dict.spares.grid.wrapper.find(".grid-delete-row").hide();
			frm.fields_dict.spares.grid.wrapper.find(".grid-insert-row-below").hide();
			frm.fields_dict.spares.grid.wrapper.find(".grid-insert-row").hide();
			frm.fields_dict.spares.grid.wrapper.find(".grid-duplicate-row").hide();
			frm.fields_dict.spares.grid.wrapper.find(".grid-move-row").hide();
		}
	},
});
