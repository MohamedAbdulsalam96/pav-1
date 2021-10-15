from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Opportunity"),
			"items": [
				{
					"type": "doctype",
					"name": "Opportunity Schedule",
					"description":_("Opportunity Schedule"),
					"onboard": 1,
					"dependencies": ["Opportunity"],
				},
			]
		}
	]