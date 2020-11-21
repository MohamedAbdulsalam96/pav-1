from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Accounting"),
			"items": [
				{
					"type": "doctype",
					"name": "Advance Request",
					"description":_("Advance Request"),
					"onboard": 1,
					"dependencies": ["Mode of Payment"],
				},
				{
					"type": "doctype",
					"name": "Expense Entry",
					"description":_("Expense Entry"),
					"onboard": 1,
					"dependencies": ["Expense Claim Type"],
				},
				{
					"type": "doctype",
					"name": "Project Dimension",
					"description":_("Project Dimension"),
					"onboard": 1,
					"dependencies": ["Project"],
				},
				{
					"type": "doctype",
					"name": "Project Activities",
					"description":_("Project Activities"),
					"onboard": 1,
					"dependencies": ["Project Dimension"],
				},
			]
		},
		{
			"label": _("Accounting MC"),
			"items": [
				{
					"type": "doctype",
					"name": "Advance Request MC",
					"description":_("Advance Request MC"),
					"onboard": 1,
					"dependencies": ["Mode of Payment", "Employee"],
				},
				{
					"type": "doctype",
					"name": "Expense Entry MC",
					"description":_("Expense Entry MC"),
					"onboard": 1,
					"dependencies": ["Expense Type MC"],
				},
				{
					"type": "doctype",
					"name": "Expense Type MC",
					"description":_("Expense Type MC"),
					"onboard": 1,
					"dependencies": ["Account"],
				},
				{
					"type": "report",
					"name": "Trial Balance for Employee MC",
					"doctype": "GL Entry",
					"is_query_report": True
				},
			]
		},
		{
			"label": _("HR"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee Checkin Manual",
					"description":_("Employee Checkin Manual"),
					"onboard": 1,
					"dependencies": ["Employee"],
				},
				{
					"type": "doctype",
					"name": "Employee Checkin Request",
					"description":_("Employee Checkin Request"),
					"onboard": 1,
					"dependencies": ["Employee"],
				},
				{
					"type": "doctype",
					"name": "Payroll Entry Tool",
					"description":_("Payroll Entry Tool"),
					"onboard": 1,
					"dependencies": ["Payroll Entry"],
				},
			]
		},
		{
			"label": _("Report"),
			"items": [
				{
					"type": "report",
					"name": "Trial Balance for Party in Party Currency",
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
			]
		},

		{
			"label": _("Setup"),
			"items": [
				{
					"type": "doctype",
					"name": "Project Activity Settings",
					"description":_("Project Activity Settings")
				}
			]
		},
	]