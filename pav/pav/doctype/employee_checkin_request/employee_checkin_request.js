// Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee Checkin Request', {
	employee: function(frm) {
		frm.trigger("set_leave_approver");
	},
	setup: function(frm) {
		frm.set_query("checkin_approver", function() {
			return {
				query: "erpnext.hr.doctype.department_approver.department_approver.get_approvers",
				filters: {
					employee: frm.doc.employee,
					doctype: 'Leave Application'
				}
			};
		});

		frm.set_query("employee", erpnext.queries.employee);
	},
	set_leave_approver: function(frm) {
		if(frm.doc.employee) {
			// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: 'erpnext.hr.doctype.leave_application.leave_application.get_leave_approver',
				args: {
					"employee": frm.doc.employee,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value('checkin_approver', r.message);
					}
				}
			});
		}
	}
});
