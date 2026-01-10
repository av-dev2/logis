// Copyright (c) 2025, elius mgani and contributors
// For license information, please see license.txt

frappe.ui.form.on("Maintenance Record", {
	setup: (frm) => {
		frm.trigger('validate_add_spare');
	},

	refresh: (frm) => {
		frm.trigger('validate_add_spare');
	},

    onload: (frm) => {
        frm.trigger('validate_add_spare');
    },

	validate_add_spare: (frm) => {
        frm.get_field("spares").grid.cannot_add_rows = true;

        $("*[data-fieldname='spares']").find(".grid-remove-rows").hide();
        $("*[data-fieldname='spares']").find(".grid-remove-all-rows").hide();
	},
});

// Add auto-fetch for item details in spares table
frappe.ui.form.on('Maintenance Spare Detail', {
    form_render: (frm, cdt, cdn) => {
        frm.fields_dict.spares.grid.wrapper.find(".grid-delete-row").hide();
        frm.fields_dict.spares.grid.wrapper.find(".grid-insert-row-below").hide();
        frm.fields_dict.spares.grid.wrapper.find(".grid-insert-row").hide();
        frm.fields_dict.spares.grid.wrapper.find(".grid-duplicate-row").hide();
        frm.fields_dict.spares.grid.wrapper.find(".grid-move-row").hide();
    },

    qty_used: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        let qty_provided = row.qty_provided || 0;
        let qty_used = row.qty_used || 0;

        if (qty_used > qty_provided) {
            frappe.msgprint({
                title: __('Invalid Quantity'),
                indicator: 'red',
                message: __('Row {0}: Qty Used ({1}) cannot be greater than Qty Provided ({2}) for spare <b>{3}</b>.', 
                    [row.idx, qty_used, qty_provided, row.spare])
            });
            frappe.model.set_value(cdt, cdn, 'qty_used', 0);
            return;
        }

        let remained_qty = qty_provided - qty_used;
        frappe.model.set_value(cdt, cdn, 'remained_qty', remained_qty);
    },
});
