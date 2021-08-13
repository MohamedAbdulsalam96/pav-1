from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'loans_entry',
		'transactions': [
			{
				'label': _('Loan'),
				'items': ['Loan']
			},
		]
	}
