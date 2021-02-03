// Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payroll Entry Tool', {
	setup: function(frm) {
		frm.add_fetch("company", "cost_center", "cost_center");
		frm.add_fetch("company", "sun_cost_center", "sun_cost_center");
		frm.add_fetch("company", "round_off_account", "round_off_account");
		frm.add_fetch("company", "default_payroll_payable_account", "payroll_account");
		frm.fields_dict['payroll_entry'].get_query = function () {
			return {
				filters: {
					"docstatus": 1,
					"salary_slips_submitted":1
				}
			}
		}
		frm.fields_dict['project_activities'].get_query = function () {
			return {
				filters: {
					"project": frm.doc.project
				}
			}
		}
		frm.fields_dict['payroll_payable_account'].get_query = function () {
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

	},
	currency: function(frm){
		var cc=''		
		console.log(cc)
		if (frm.doc.currency && frm.doc.company){
			cc=frappe.db.get_value("Company", {'name':frm.doc.company}, "default_currency")
		        frappe.db.get_value('Company', {'name':frm.doc.company}, "default_currency").then(({ message }) => {
		        if (message) {
			        cc=message.default_currency;
				frm.set_df_property('conversion_rate',  'hidden',  frm.doc.currency==cc ? 1 : 0);
				console.log(cc)
				if(frm.doc.currency && frm.doc.currency!=cc && frm.doc.company){
					frappe.call({
						method: "erpnext.setup.utils.get_exchange_rate",
			                        	args: {
			                                	from_currency: frm.doc.currency,
				                                to_currency: cc,
			        	                        transaction_date: frm.doc.posting_date
							},
							callback: function (r, rt) {
								if (r){
									frm.set_value("conversion_rate", r.message);
								}
								else{
									frm.set_value("conversion_rate", 1);
								}                                	
			                            	}
						}
					)	
				}else{
					frm.set_value("conversion_rate", 1);
				}
		        }})
	        }
	}
});
