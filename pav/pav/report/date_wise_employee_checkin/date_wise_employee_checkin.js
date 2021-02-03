// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Date wise Employee Checkin"] = {
	"filters": [
		{
			fieldname: 'employee',
			label: __('Employee'),
			fieldtype: 'Link',
			options: 'Employee'
		},
		{
			"fieldname":"from",
			"label": __("From"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"to",
			"label": __("To"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		}		
	]
};
