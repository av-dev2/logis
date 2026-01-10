# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Coalesce
from pypika import Order


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"width": 110
		},
		{
			"fieldname": "date_requested",
			"label": _("Date Requested"),
			"fieldtype": "Date",
			"width": 110
		},
		{
			"fieldname": "truck_trailer",
			"label": _("Truck/Trailer"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "spare",
			"label": _("Spare"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 200
		},
		{
			"fieldname": "qty_requested",
			"label": _("Qty Requested"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "qty_provided",
			"label": _("Qty Provided"),
			"fieldtype": "Float",
			"width": 110
		},
		{
			"fieldname": "qty_used",
			"label": _("Qty Used"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "qty_remained",
			"label": _("Qty Remained"),
			"fieldtype": "Float",
			"width": 110
		}
	]


def get_data(filters):
	data = []
	status_filter = filters.get("status") if filters else None

	# Determine which data sources to query based on status filter
	fetch_completed = not status_filter or status_filter == "Completed"
	fetch_in_progress = not status_filter or status_filter == "In Progress"
	fetch_pending = not status_filter or status_filter == "Pending"

	# 1. Fetch Completed records (Submitted Maintenance Records)
	if fetch_completed:
		completed_data = get_completed_records(filters)
		data.extend(completed_data)

	# 2. Fetch In Progress records
	# - Draft Maintenance Records
	# - Submitted Maintenance Requests with no linked Maintenance Record
	if fetch_in_progress:
		in_progress_data = get_in_progress_records(filters)
		data.extend(in_progress_data)

	# 3. Fetch Pending records (Draft Maintenance Requests)
	if fetch_pending:
		pending_data = get_pending_records(filters)
		data.extend(pending_data)

	return data


def get_completed_records(filters):
	"""Get submitted Maintenance Records (docstatus = 1) - Status: Completed"""
	data = []
	
	MaintenanceRecord = DocType("Maintenance Record")
	
	query = (
		frappe.qb.from_(MaintenanceRecord)
		.select(
			MaintenanceRecord.name,
			MaintenanceRecord.posting_date,
			MaintenanceRecord.date_requested,
			MaintenanceRecord.truck,
			MaintenanceRecord.trailer
		)
		.where(MaintenanceRecord.docstatus == 1)
	)
	
	query = apply_maintenance_record_filters(query, MaintenanceRecord, filters)
	query = query.orderby(MaintenanceRecord.posting_date, order=Order.desc)
	query = query.orderby(MaintenanceRecord.name)
	
	maintenance_records = query.run(as_dict=True)

	for record in maintenance_records:
		truck_trailer = record.truck or record.trailer or ""
		parent_id = f"MR-{record.name}"
		
		# Parent row
		data.append({
			"posting_date": record.posting_date,
			"date_requested": record.date_requested,
			"truck_trailer": truck_trailer,
			"status": "Completed",
			"spare": "",
			"qty_requested": None,
			"qty_provided": None,
			"qty_used": None,
			"qty_remained": None,
			"indent": 0,
			"id": parent_id,
			"parent_id": ""
		})

		# Get spares for this Maintenance Record
		spares = get_maintenance_record_spares(record.name)

		for idx, spare in enumerate(spares):
			data.append({
				"posting_date": None,
				"date_requested": None,
				"truck_trailer": "",
				"status": "",
				"spare": spare.spare,
				"qty_requested": spare.qty_requested,
				"qty_provided": spare.qty_provided,
				"qty_used": spare.qty_used,
				"qty_remained": spare.remained_qty,
				"indent": 1,
				"id": f"{parent_id}-{idx}",
				"parent_id": parent_id
			})

	return data


def get_in_progress_records(filters):
	"""
	Get In Progress records:
	1. Draft Maintenance Records (docstatus = 0)
	2. Submitted Maintenance Requests with no linked Maintenance Record
	"""
	data = []

	# 1. Draft Maintenance Records
	MaintenanceRecord = DocType("Maintenance Record")
	
	query = (
		frappe.qb.from_(MaintenanceRecord)
		.select(
			MaintenanceRecord.name,
			MaintenanceRecord.posting_date,
			MaintenanceRecord.date_requested,
			MaintenanceRecord.truck,
			MaintenanceRecord.trailer
		)
		.where(MaintenanceRecord.docstatus == 0)
	)
	
	query = apply_maintenance_record_filters(query, MaintenanceRecord, filters)
	query = query.orderby(MaintenanceRecord.posting_date, order=Order.desc)
	query = query.orderby(MaintenanceRecord.name)
	
	draft_records = query.run(as_dict=True)

	for record in draft_records:
		truck_trailer = record.truck or record.trailer or ""
		parent_id = f"MR-DRAFT-{record.name}"
		
		# Parent row
		data.append({
			"posting_date": record.posting_date,
			"date_requested": record.date_requested,
			"truck_trailer": truck_trailer,
			"status": "In Progress",
			"spare": "",
			"qty_requested": None,
			"qty_provided": None,
			"qty_used": None,
			"qty_remained": None,
			"indent": 0,
			"id": parent_id,
			"parent_id": ""
		})

		# Get spares for this draft Maintenance Record
		spares = get_maintenance_record_spares(record.name)

		for idx, spare in enumerate(spares):
			data.append({
				"posting_date": None,
				"date_requested": None,
				"truck_trailer": "",
				"status": "",
				"spare": spare.spare,
				"qty_requested": spare.qty_requested,
				"qty_provided": spare.qty_provided,
				"qty_used": spare.qty_used,
				"qty_remained": spare.remained_qty,
				"indent": 1,
				"id": f"{parent_id}-{idx}",
				"parent_id": parent_id
			})

	# 2. Submitted Maintenance Requests with no linked Maintenance Record
	linked_request_names = get_linked_maintenance_requests()

	MaintenanceRequest = DocType("Maintenance Request")
	
	query = (
		frappe.qb.from_(MaintenanceRequest)
		.select(
			MaintenanceRequest.name,
			MaintenanceRequest.posting_date,
			MaintenanceRequest.truck,
			MaintenanceRequest.trailer
		)
		.where(MaintenanceRequest.docstatus == 1)
	)
	
	if linked_request_names:
		query = query.where(MaintenanceRequest.name.notin(linked_request_names))
	
	query = apply_maintenance_request_filters(query, MaintenanceRequest, filters)
	query = query.orderby(MaintenanceRequest.posting_date, order=Order.desc)
	query = query.orderby(MaintenanceRequest.name)
	
	submitted_requests = query.run(as_dict=True)

	for request in submitted_requests:
		truck_trailer = request.truck or request.trailer or ""
		parent_id = f"MREQ-IP-{request.name}"
		
		# Parent row - using posting_date as date_requested since Maintenance Request doesn't have date_requested
		data.append({
			"posting_date": request.posting_date,
			"date_requested": request.posting_date,  # Use posting_date as date_requested
			"truck_trailer": truck_trailer,
			"status": "In Progress",
			"spare": "",
			"qty_requested": None,
			"qty_provided": None,
			"qty_used": None,
			"qty_remained": None,
			"indent": 0,
			"id": parent_id,
			"parent_id": ""
		})

		# Get spares for this Maintenance Request
		spares = get_maintenance_request_spares(request.name)

		for idx, spare in enumerate(spares):
			data.append({
				"posting_date": None,
				"date_requested": None,
				"truck_trailer": "",
				"status": "",
				"spare": spare.spare,
				"qty_requested": spare.qty_requested,
				"qty_provided": spare.qty_provided,
				"qty_used": None,
				"qty_remained": None,
				"indent": 1,
				"id": f"{parent_id}-{idx}",
				"parent_id": parent_id
			})

	return data


def get_pending_records(filters):
	"""Get Draft Maintenance Requests (docstatus = 0) - Status: Pending"""
	data = []
	
	MaintenanceRequest = DocType("Maintenance Request")
	
	query = (
		frappe.qb.from_(MaintenanceRequest)
		.select(
			MaintenanceRequest.name,
			MaintenanceRequest.posting_date,
			MaintenanceRequest.truck,
			MaintenanceRequest.trailer
		)
		.where(MaintenanceRequest.docstatus == 0)
	)
	
	query = apply_maintenance_request_filters(query, MaintenanceRequest, filters)
	query = query.orderby(MaintenanceRequest.posting_date, order=Order.desc)
	query = query.orderby(MaintenanceRequest.name)
	
	draft_requests = query.run(as_dict=True)

	for request in draft_requests:
		truck_trailer = request.truck or request.trailer or ""
		parent_id = f"MREQ-P-{request.name}"
		
		# Parent row - using posting_date as date_requested since Maintenance Request doesn't have date_requested
		data.append({
			"posting_date": request.posting_date,
			"date_requested": request.posting_date,  # Use posting_date as date_requested
			"truck_trailer": truck_trailer,
			"status": "Pending",
			"spare": "",
			"qty_requested": None,
			"qty_provided": None,
			"qty_used": None,
			"qty_remained": None,
			"indent": 0,
			"id": parent_id,
			"parent_id": ""
		})

		# Get spares for this Maintenance Request
		spares = get_maintenance_request_spares(request.name)

		for idx, spare in enumerate(spares):
			data.append({
				"posting_date": None,
				"date_requested": None,
				"truck_trailer": "",
				"status": "",
				"spare": spare.spare,
				"qty_requested": spare.qty_requested,
				"qty_provided": spare.qty_provided,
				"qty_used": None,
				"qty_remained": None,
				"indent": 1,
				"id": f"{parent_id}-{idx}",
				"parent_id": parent_id
			})

	return data


def get_maintenance_record_spares(parent_name):
	"""Get spares for a Maintenance Record"""
	MaintenanceRecordSpare = DocType("Maintenance Record Spare")
	
	return (
		frappe.qb.from_(MaintenanceRecordSpare)
		.select(
			MaintenanceRecordSpare.spare,
			MaintenanceRecordSpare.qty_requested,
			MaintenanceRecordSpare.qty_provided,
			MaintenanceRecordSpare.qty_used,
			MaintenanceRecordSpare.remained_qty
		)
		.where(MaintenanceRecordSpare.parent == parent_name)
		.run(as_dict=True)
	)


def get_maintenance_request_spares(parent_name):
	"""Get spares for a Maintenance Request"""
	MaintenanceSpareDetail = DocType("Maintenance Spare Detail")
	
	return (
		frappe.qb.from_(MaintenanceSpareDetail)
		.select(
			MaintenanceSpareDetail.spare,
			MaintenanceSpareDetail.qty_requested,
			MaintenanceSpareDetail.qty_provided
		)
		.where(MaintenanceSpareDetail.parent == parent_name)
		.run(as_dict=True)
	)


def get_linked_maintenance_requests():
	"""Get all Maintenance Requests that are linked to any Maintenance Record"""
	MaintenanceRecordDetail = DocType("Maintenance Record Detail")
	MaintenanceRecord = DocType("Maintenance Record")
	
	linked_requests = (
		frappe.qb.from_(MaintenanceRecordDetail)
		.inner_join(MaintenanceRecord)
		.on(MaintenanceRecord.name == MaintenanceRecordDetail.parent)
		.select(MaintenanceRecordDetail.maintenance_request)
		.distinct()
		.run(as_dict=True)
	)
	
	return [r.maintenance_request for r in linked_requests if r.maintenance_request]


def apply_maintenance_record_filters(query, doctype, filters):
	"""Apply filters for Maintenance Record (includes date_requested filter)"""
	if not filters:
		return query
	
	if filters.get("truck"):
		query = query.where(doctype.truck == filters.get("truck"))
	
	if filters.get("trailer"):
		query = query.where(doctype.trailer == filters.get("trailer"))
	
	if filters.get("posting_date_from"):
		query = query.where(doctype.posting_date >= filters.get("posting_date_from"))
	
	if filters.get("posting_date_to"):
		query = query.where(doctype.posting_date <= filters.get("posting_date_to"))
	
	# date_requested filter only applies to Maintenance Record
	if filters.get("date_requested_from"):
		query = query.where(doctype.date_requested >= filters.get("date_requested_from"))
	
	if filters.get("date_requested_to"):
		query = query.where(doctype.date_requested <= filters.get("date_requested_to"))
	
	return query


def apply_maintenance_request_filters(query, doctype, filters):
	"""Apply filters for Maintenance Request (excludes date_requested filter)"""
	if not filters:
		return query
	
	if filters.get("truck"):
		query = query.where(doctype.truck == filters.get("truck"))
	
	if filters.get("trailer"):
		query = query.where(doctype.trailer == filters.get("trailer"))
	
	if filters.get("posting_date_from"):
		query = query.where(doctype.posting_date >= filters.get("posting_date_from"))
	
	if filters.get("posting_date_to"):
		query = query.where(doctype.posting_date <= filters.get("posting_date_to"))
	
	# Note: date_requested filter is NOT applied to Maintenance Request
	
	return query
