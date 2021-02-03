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
			]
		},
	]