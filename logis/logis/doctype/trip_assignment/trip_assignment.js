// Copyright (c) 2025, elius mgani and contributors
// For license information, please see license.txt

frappe.ui.form.on("Trip Assignment", {
    setup: (frm) => {
        if (!frm.doc.company) {
            frm.set_value("company", frappe.defaults.get_default("company"));
        }

        if (!frm.doc.posting_date) {
            frm.set_value("posting_date", frappe.datetime.get_today());
        }
    },
	refresh: (frm) => {
        frm.trigger("set_filters");
	},
    onload: (frm) => {
        frm.trigger("set_filters");
    },
    set_filters: (frm) => {
        frm.set_query("truck", () => {
            return {
                filters: {
                    disabled: 0
                }
            };
        })

        frm.set_query("trailer", () => {
            return {
                filters: {
                    disabled: 0
                }
            };
        })

        frm.set_query("driver", () => {
            return {
                filters: {
                    status: 'Active'
                }
            };
        })

        frm.set_query("fuel_type", () => {
            return {
                filters: {
                    item_group: "Fuel"
                }
            };
        })
    }
});
