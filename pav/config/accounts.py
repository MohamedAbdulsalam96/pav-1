from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("PAV Settings"),
			"items": [				
				{
					"type": "doctype",
					"name": "Employee Account",
					"description":_("Employee Account"),
					"onboard": 1,
					"dependencies": ["Employee"],
				},
				{
					"type": "doctype",
					"name": "Project Activities",
					"description":_("Project Activities"),
					"onboard": 1,
					"dependencies": ["Project"],
				},
				{
					"type": "doctype",
					"name": "PAV Settings",
					"description":_("PAV Settings"),										
				},
			]
		},
		{
			"label": _("PAV Transactions"),
			"items": [
				{
					"type": "doctype",
					"name": "Advance Request",
					"description":_("Advance Request"),
					"onboard": 1,
					"dependencies": ["Employee"],
				},
				{
					"type": "doctype",
					"name": "Expense Entry",
					"description":_("Expense Entry"),
					"onboard": 1,
					"dependencies": ["Employee"],
				},
			]
		},
		{
			"label": _("PAV Reports"),
			"items": [
				{
					"type": "report",
					"name": "Currency wise General Ledger",
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Trial Balance for Party in Party Currency",
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Trial Balance for Multi Party in Party Currency",
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Trial Balance for Employee MC",
					"doctype": "GL Entry",
					"is_query_report": True
				},			
				{
					"type": "report",
					"name": "Budget Variance Report for Project Activities",
					"doctype": "Project Activities",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Project Activity-wise Salary Register",
					"doctype": "Salary Slip",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Project-wise Salary Register",
					"doctype": "Salary Slip",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounting Dimension Balance",
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounting Dimension wise Stock Planned and Actual",
					"doctype": "Stock Ledger Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Trial Balance MC",
					"doctype": "GL Entry",
					"is_query_report": True
				},
			]
		},
		{
			"label": _("PAV Tools"),
			"items": [
				{
					"type": "doctype",
					"name": "Payroll Entry Tool",
					"description":_("Payroll Entry Tool"),
					"onboard": 1,
					"dependencies": ["Payroll Entry"],
				}				
			]
		},
	]