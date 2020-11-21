// Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Salary Tool', {
	setup: function(frm) {
		frm.add_fetch("company", "cost_center", "cost_center");
		frm.fields_dict['payroll_payable_account'].get_query = function () {
			return {
				filters: {
					"account_type": 'Payable'
				}
			}
		}
		frm.fields_dict['expense_account'].get_query = function () {
			return {
				filters: {
					"account_type": 'Expense Account'
				}
			}
		}
	},
	refresh: function(frm) {
		if (frm.doc.docstatus == 0) {
			if(!frm.is_new()) {
				frm.page.clear_primary_action();
				frm.add_custom_button(__("Get Employees"),
					function() {
						frm.events.get_employee_details(frm);
					}
				).toggleClass('btn-primary', !(frm.doc.employees || []).length);
			}
			if ((frm.doc.employees || []).length) {
				frm.page.set_primary_action(__('Create Accrual JV'), () => {
					frm.save('Submit').then(()=>{
						frm.page.clear_primary_action();
						frm.refresh();
						frm.events.refresh(frm);
					});
				});
			}
		}
	},
	get_employee_details: function (frm) {
		return frappe.call({
			doc: frm.doc,
			method: 'fill_employee_details',
			callback: function(r) {
				if (r.docs[0].employees){
					frm.save();
					frm.refresh();
				}
			}
		})
	},
});