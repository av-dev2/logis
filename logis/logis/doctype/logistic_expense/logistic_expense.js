// Copyright (c) 2025, elius mgani and contributors
// For license information, please see license.txt

frappe.ui.form.on("Logistic Expense", {
	refresh: (frm) => {
        frm.trigger("set_filters");
	},
    onload: (frm) => {
        frm.trigger("set_filters");
    },
    set_filters: (frm) => {
        frm.set_query("expense_account", () => {
            return {
                filters: {
                    root_type: 'Expense',
                }
            };
        })
    }
});
