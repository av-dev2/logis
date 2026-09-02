// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

frappe.query_reports["Maintenance Report"] = {
	filters: [
		{
			fieldname: "truck",
			label: __("Truck"),
			fieldtype: "Link",
			options: "Truck",
		},
		{
			fieldname: "trailer",
			label: __("Trailer"),
			fieldtype: "Link",
			options: "Trailer",
		},
		{
			fieldname: "posting_date_from",
			label: __("Posting Date From"),
			fieldtype: "Date",
		},
		{
			fieldname: "posting_date_to",
			label: __("Posting Date To"),
			fieldtype: "Date",
		},
		{
			fieldname: "date_requested_from",
			label: __("Date Requested From"),
			fieldtype: "Date",
		},
		{
			fieldname: "date_requested_to",
			label: __("Date Requested To"),
			fieldtype: "Date",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nPending\nIn Progress\nCompleted",
		},
	],
	tree: true,
	name_field: "id",
	parent_field: "parent_id",
	initial_depth: 1,
};
