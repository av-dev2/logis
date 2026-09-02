// Copyright (c) 2025, Administrator and contributors
// For license information, please see license.txt

frappe.ui.form.on("Trip Settlement", {
	refresh: (frm) => {
		frm.trigger("set_query");
	},

	onload: (frm) => {
		frm.trigger("set_query");
	},

	set_query: (frm) => {
		frm.set_query("trip_assignment", () => {
			return {
				filters: {
					settled: 0,
				},
			};
		});
	},
});
