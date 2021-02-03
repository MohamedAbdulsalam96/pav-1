from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Expenses"),
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
	]