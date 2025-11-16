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
    expected_trips: (frm) => {
        frm.trigger("set_requested_fuel");
    },
    fuel_per_trip: (frm) => {
        frm.trigger("set_requested_fuel");
    },
    requested_fuel: (frm) => {
        const total_fuel = (frm.doc.requested_fuel || 0) + (frm.doc.previous_remained_fuel || 0);
        frm.set_value("total_fuel", total_fuel);
    },
    previous_remained_fuel: (frm) => {
        const total_fuel = (frm.doc.requested_fuel || 0) + (frm.doc.previous_remained_fuel || 0);
        frm.set_value("total_fuel", total_fuel);
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
    },
    set_requested_fuel: (frm) => {
        const total_fuel = (frm.doc.expected_trips || 0) * (frm.doc.fuel_per_trip || 0);
        frm.set_value("requested_fuel", total_fuel);
    },
    calculate_total_expense: (frm) => {
        let total = 0;
        if (frm.doc.expenses) {
            frm.doc.expenses.forEach((row) => {
                total += (row.amount || 0);
            });
        }
        frm.set_value("total_expense", total);
    }
});

frappe.ui.form.on("Trip Assignment Expense", {
    expenses_add: (frm) => {
        frm.trigger("calculate_total_expense");
    },
    expenses_remove: (frm) => {
        frm.trigger("calculate_total_expense");
    },
    amount: (frm) => {
        frm.trigger("calculate_total_expense");
    }
});
