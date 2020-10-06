// Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payroll Entry Tool', {
	setup: function(frm) {
		frm.fields_dict['project_activities'].get_query = function () {
			return {
				filters: {
					"project": frm.doc.project
				}
			}
		}
		frm.fields_dict['payroll_account'].get_query = function () {
			return {
				filters: {
					"account_type": 'Payable'
				}
			}
		}
		frm.fields_dict['payment_account'].get_query = function () {
			return {
				filters: {
					"account_type": ['in',['Cash','Bank']]
				}
			}
		}

	}
});
