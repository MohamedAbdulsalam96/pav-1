from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Attendance"),
			"items": [
				{
					"type": "doctype",
					"name": "Travel Request",
					"description":_("Travel Request"),
					"onboard": 1,
					"dependencies": ["Employee"],
				},
				{
					"type": "report",
					"name": "Employee Checkin Summery Report",
					"doctype": "Employee",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Date wise Employee Checkin",
					"doctype": "Employee Checkin",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Cumulative Attendance Report",
					"doctype": "Employee",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Employee Leave and Attendance Status Report",
					"doctype": "Employee",
					"is_query_report": True
				},
			]
		},
	]