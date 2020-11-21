// Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt

frappe.provide("pav.pav");

cur_frm.cscript.set_help = function (doc) {
	cur_frm.set_intro("");
	if (doc.__islocal && !in_list(frappe.user_roles, "HR User")) {
		cur_frm.set_intro(__("Fill the form and save it"));
	}
};


frappe.ui.form.on('Expense Entry Detail MC', {
	amount: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if(child.amount && frm.doc.currency){
	        	frappe.model.set_value(cdt, cdn, 'base_amount',child.amount * frm.doc.conversion_rate)
		}else{
			frappe.msgprint(__("Please set the Currency & Amount First"));
	    		return;
		}
	},
})

frappe.ui.form.on('Expense Entry MC', {
	refresh: function(frm) {
		frm.set_df_property('currency',  'read_only',  frm.doc.type=='Employee'? 0 : 1);
		if (!frm.is_new()){
			frappe.db.get_value("Company", {"name": frm.doc.company}, "default_currency", function(value) {
				frm.set_df_property('conversion_rate',  'hidden',  value.default_currency==frm.doc.currency?1:0);
				frm.set_df_property('base_amount',  'hidden',  value.default_currency==frm.doc.currency?1:0);
			});
		}else{
			frm.set_df_property('title',  'read_only',  1);
			frm.set_value("title", (frm.doc.task)?frm.doc.task+" Expenses":"Test Title");
		}
        	if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Accounting Ledger'), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					company: frm.doc.company,
					group_by_voucher: false
				};
			frappe.set_route("query-report", "General Ledger");
			}, __("View"));
	       	}
	},
	validate: function(frm) {
		$.each((frm.doc.expenses || []), function (i, d) {
        		frm.doc.amount += d.amount;
		        frm.doc.base_amount += d.base_amount;
		});
	},
	type: function(frm) {
		frm.set_df_property('currency',  'read_only',  frm.doc.type=='Employee'? 0 : 1);
		frm.trigger("fill_to_account")
	},
	mode_of_payment: function(frm) {
		frm.trigger("fill_to_account")
	},
	bank_account: function(frm) {
		frm.trigger("fill_to_account")
	},
	employee: function(frm) {
		frm.trigger("fill_to_account")
	},
	check_to_account: function(frm) {
		if(!frm.doc.company){
			frappe.msgprint(__("Please Set the Company First"));
			frm.refresh_fields();
			return;
		}
		if(!frm.doc.payment_account){
			frappe.msgprint(__("Please Set the Payment Account First"));
			frm.refresh_fields();
			return;
		}

	},
	fill_to_account: function(frm) {
		console.log('dd')
		frm.set_df_property('currency',  'read_only',  frm.doc.type=='Employee'? 0 : 1);
		if(!frm.doc.company){
			frappe.msgprint(__("Please Set the Company First"));
			frm.refresh_fields();
			return;
		}
		if(frm.doc.type=='Mode of Payment' && frm.doc.mode_of_payment){
			frm.set_value("bank_account", '');
			frm.set_value("employee", '');
			frm.set_value("payment_account", '');
		        frappe.call({
				method: "pav.pav.doctype.advance_request_mc.advance_request_mc.get_payment_account",
				args: {
					"mode_of_payment": frm.doc.mode_of_payment,
					"company": frm.doc.company
            			},
            			callback: function (r) {
                			if (r.message) {
                    				frm.set_value("payment_account", r.message.account);
                    				frm.set_value("currency", r.message.account_currency);
						frappe.db.get_value("Company", {"name": frm.doc.company}, "default_currency", function(value) {
							if (r.message.account_currency!=value.default_currency){
								frm.set_df_property('conversion_rate',  'hidden',  0);
					                        frappe.call({
									method: "erpnext.setup.utils.get_exchange_rate",
									args: {
						                                from_currency: r.message.account_currency,
										to_currency: value.default_currency,
										transaction_date: frm.doc.posting_date
									},
									callback: function (r, rt) {
										frm.set_value("conversion_rate", r.message);
									}
								})
							}else{
								frm.set_value("conversion_rate", 1);
								frm.set_df_property('conversion_rate',  'hidden',  1);
							}
						});
					}
				}
			});
		}
		else if(frm.doc.type=='Bank Account' && frm.doc.bank_account){
			frm.set_value("mode_of_payment", '');
			frm.set_value("employee", '');
			frm.set_value("payment_account", '');
			frappe.db.get_value("Bank Account", {"name": frm.doc.bank_account}, "account", function(value) {
				frm.set_value("payment_account", value.account);
				frappe.db.get_value("Account", {"name": value.account}, "account_currency", function(value2) {
					frm.set_value("currency", value2.account_currency);
					frappe.db.get_value("Company", {"name": frm.doc.company}, "default_currency", function(value3) {
						if (value2.account_currency!=value3.default_currency){
							frm.set_df_property('conversion_rate',  'hidden',  0);
					                       frappe.call({
								method: "erpnext.setup.utils.get_exchange_rate",
								args: {
					                                from_currency: value2.account_currency,
									to_currency: value3.default_currency,
									transaction_date: frm.doc.posting_date
								},
								callback: function (r, rt) {
									frm.set_value("conversion_rate", r.message);
								}
							})
						}else{
							frm.set_value("conversion_rate", 1);
							frm.set_df_property('conversion_rate',  'hidden',  1);
						}
					});
				});

			});
		}
		else if(frm.doc.type=='Employee'){
			frm.set_value("mode_of_payment", '');
			frm.set_value("bank_account", '');
			frm.set_value("payment_account", '');
			frappe.db.get_value("Company", {"name": frm.doc.company}, "default_employee_payable_account_mc_pav", function(value) {
				if (value.default_employee_payable_account_mc_pav){
					frm.set_value("payment_account", value.default_employee_payable_account_mc_pav);
				}else{
					frappe.msgprint(__("Please Set Default Employee Payable Account MC PAV in the Company"));
				}
			});
		}else{
			frm.set_value("payment_account", '');
		}
		frm.refresh_fields();
	},
	currency: function(frm) {
		if (frm.doc.currency){
			frappe.db.get_value("Company", {"name": frm.doc.company}, "default_currency", function(value) {
				if (frm.doc.currency!=value.default_currency){
					frm.set_df_property('conversion_rate',  'hidden',  0);
					         frappe.call({
							method: "erpnext.setup.utils.get_exchange_rate",
							args: {
								from_currency: frm.doc.currency,
								to_currency: value.default_currency,
								transaction_date: frm.doc.posting_date
							},
								callback: function (r, rt) {
									frm.set_value("conversion_rate", r.message);
								}
						})
				}else{
					frm.set_value("conversion_rate", 1);
					frm.set_df_property('conversion_rate',  'hidden',  1);
				}
			});				
		}
	},


});
