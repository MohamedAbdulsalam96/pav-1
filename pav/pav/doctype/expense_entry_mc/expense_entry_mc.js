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
		if (child.amount && frm.doc.currency) {
			frappe.model.set_value(cdt, cdn, 'base_amount', child.amount * frm.doc.conversion_rate)
		} else {
			frappe.msgprint(__("Please set the Currency & Amount First"));
			return;
		}
	},
})

frappe.ui.form.on('Expense Entry MC', {
	is_paid: function (frm) {
		if (frm.doc.is_paid == 1) {
			frm.set_df_property('payment_section_section', 'hidden', 0);
			frm.set_df_property('party_account_section', 'hidden', 0);
		} else {
			frm.set_df_property('payment_section_section', 'hidden', 1);
			frm.set_df_property('party_account_section', 'hidden', 1);
			frm.set_value("from_mode_of_payment", '');
			frm.set_value("from_bank_account", '');
			frm.set_value("from_account", '');
		}
	},
	setup: function (frm) {
		frm.fields_dict['from_bank_account'].get_query = function () {
			return {
				filters: {
					"is_company_account": 1
				}
			}
		}
		frm.set_df_property('currency', 'read_only', 0);
		if (frm.doc.type){
			if (frm.doc.type=='Employee'){
				frm.set_df_property('currency', 'read_only', 0);
			}else if (frm.doc.type=='Supplier' || frm.doc.type=='Bank Account' || frm.doc.type=='Mode of Payment'){
				frm.set_df_property('currency', 'read_only', 1);
			}
		}
		if (frm.doc.is_paid == 1) {
			frm.set_df_property('payment_section_section', 'hidden', 0);
			frm.set_df_property('party_account_section', 'hidden', 0);
		} else {
			frm.set_df_property('payment_section_section', 'hidden', 1);
			frm.set_df_property('party_account_section', 'hidden', 1);
		}
		if (frm.doc.type == 'Employee' || frm.doc.type == 'Supplier') {
			
			frm.set_df_property('is_paid', 'hidden', 0);
			frm.set_df_property('party_account_section', 'hidden', 0);
			frm.fields_dict['party_bank_account'].get_query = function () {
				return {
					filters: {
						"party_type": frm.doc.type,
						"party": frm.doc.type == 'Employee' ? frm.doc.employee : frm.doc.supplier,
					}
				}
			}
		} else {
			frm.set_df_property('is_paid', 'hidden', 1);
			frm.set_df_property('party_account_section', 'hidden', 1);
		}
	},
	refresh: function (frm) {
		//frm.set_df_property('currency', 'read_only', frm.doc.type == 'Employee' ? 0 : 1);
		if (!frm.is_new()) {
			frappe.db.get_value("Company", { "name": frm.doc.company }, "default_currency", function (value) {
				frm.set_df_property('conversion_rate', 'hidden', value.default_currency == frm.doc.currency ? 1 : 0);
				frm.set_df_property('base_amount', 'hidden', value.default_currency == frm.doc.currency ? 1 : 0);
				frm.set_df_property('paid_base_amount', 'hidden', value.default_currency == frm.doc.currency ? 1 : 0);
			});
		} else {
			//frm.set_df_property('title',  'read_only',  1);
			//frm.set_value("title", frm.doc.user_remark);
		}
		if (frm.doc.docstatus === 1) {
			if (frm.doc.jv_created==0 && frm.doc.docstatus === 1 && frm.doc.status=='Approved') {
				frm.add_custom_button(__('Journal Entry'), function () {
					return frappe.call({
						doc: frm.doc,
						method: 'make_accrual_jv_entry',
						args: {
							
						},
						callback: function (r) {
							var doclist = frappe.model.sync(r.message);
							frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
						}
					});
				}, __("Create"));
			}
			if (frm.doc.jv_created==1){
				frm.add_custom_button(__('Journal Entry'), function () {					
					frappe.route_options = {
						reference_type: frm.doc.doctype,
						reference_name: frm.doc.name
					};
					frappe.set_route("List", "Journal Entry");
				}, __("View"));
			}
			frm.add_custom_button(__('Accounting Ledger'), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by_voucher: false,
					presentation_currency: frm.doc.currency
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}
	},
	validate: function (frm) {
		/*if (frm.doc.type == 'Supplier' && frm.doc.is_paid != 1) {
			frappe.msgprint(__("If the Type is Supplier, then Is Paid must be selected"));
			validated = false;
		}*/
		if (frm.doc.type != 'Supplier' && frm.doc.type != 'Employee' && frm.doc.is_paid == 1) {
			frappe.msgprint(__("Is Paid Only with Employee or Supplier"));
			validated = false;
		}
		$.each((frm.doc.expenses || []), function (i, d) {
			d.currency = frm.doc.currency
			d.base_amount=d.amount*frm.doc.conversion_rate			
			if (d.project_activities) {
				frappe.call({
					method: 'frappe.client.get_value',
					args: {
						doctype: 'Project Activities',
						filters: {
							'name': d.project_activities,
						},
						fieldname: ['project', 'project_dimension', 'customer']
					},
					callback: function (data) {
						d.customer = data.message.customer
						d.project_dimension = data.message.project_dimension
						d.project = data.message.project
					}
				})
			}
			frm.doc.amount += d.amount;
			frm.doc.base_amount += d.base_amount;

		});
		if (frm.doc.employee_name && !frm.doc.employee)
			frm.set_value('employee_name', '')
		if (frm.doc.from_account) {
			frappe.db.get_value("Account", { "name": frm.doc.from_account }, "account_currency", function (value) {
				if (value.account_currency != frm.doc.currency) {
					frappe.msgprint(__("From Account Currency should to be same of Payment Account Currency"));
					validated = false;
				}
			});
		}

	},
	type: function (frm) {
		console.log(frm.doc.type)
		//frm.set_df_property('currency', 'read_only', frm.doc.type == 'Employee' ? 0 : 1);
		frm.trigger("fill_to_account")
		frm.set_df_property('currency', 'read_only', 0);
		if (frm.doc.type){
			if (frm.doc.type=='Employee'){
				frm.set_df_property('currency', 'read_only', 0);
			}else if (frm.doc.type=='Supplier' || frm.doc.type=='Bank Account' || frm.doc.type=='Mode of Payment'){
				frm.set_df_property('currency', 'read_only', 1);
			}
		}
		if (frm.doc.type == 'Employee' || frm.doc.type == 'Supplier') {
			frm.set_df_property('is_paid', 'hidden', 0);
			frm.set_df_property('party_account_section', 'hidden', 0);
			frm.fields_dict['party_bank_account'].get_query = function () {
				return {
					filters: {
						"party_type": frm.doc.type,
						"party": frm.doc.type == 'Employee' ? frm.doc.employee : frm.doc.supplier,
					}
				}
			}
		} else {
			frm.set_df_property('is_paid', 'hidden', 1);
			frm.set_df_property('party_account_section', 'hidden', 1);
		}
		
	},
	mode_of_payment: function (frm) {
		frm.trigger("fill_to_account")
	},
	bank_account: function (frm) {
		frm.trigger("fill_to_account")
	},
	employee: function (frm) {
		frm.trigger("fill_to_account")
	},
	supplier: function (frm) {
		frm.trigger("fill_to_account")
	},
	project_dimension: function (frm) {
		frm.set_value("project", '');
	},
	check_to_account: function (frm) {
		if (!frm.doc.company) {
			frappe.msgprint(__("Please Set the Company First"));
			frm.refresh_fields();
			return;
		}
		if (!frm.doc.payment_account) {
			frappe.msgprint(__("Please Set the Payment Account First"));
			frm.refresh_fields();
			return;
		}

	},
	fill_to_account: function (frm) {
		console.log('dd')
		//frm.set_df_property('currency', 'read_only', frm.doc.type == 'Employee' ? 0 : 1);
		if (!frm.doc.company) {
			frappe.msgprint(__("Please Set the Company First"));
			frm.refresh_fields();
			return;
		}
		if (frm.doc.type == 'Mode of Payment' && frm.doc.mode_of_payment) {
			frm.set_value("bank_account", '');
			frm.set_value("employee", '');
			frm.set_value("payment_account", '');
			frm.set_value('employee_name', '')
			frm.set_value('supplier', '')
			frm.set_value('supplier_name', '')
			frm.set_value('is_paid', 0)
			frm.set_value('party_bank_account',)
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
						frappe.db.get_value("Company", { "name": frm.doc.company }, "default_currency", function (value) {
							if (r.message.account_currency != value.default_currency) {
								frm.set_df_property('conversion_rate', 'hidden', 0);
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
							} else {
								frm.set_value("conversion_rate", 1);
								frm.set_df_property('conversion_rate', 'hidden', 1);
							}
						});
					}
				}
			});
		}
		else if (frm.doc.type == 'Bank Account' && frm.doc.bank_account) {
			frm.set_value("mode_of_payment", '');
			frm.set_value("employee", '');
			frm.set_value("payment_account", '');
			frm.set_value('employee_name', '')
			frm.set_value('supplier', '')
			frm.set_value('supplier_name', '')
			frm.set_value('is_paid', 0)
			frm.set_value('party_bank_account',)
			frappe.db.get_value("Bank Account", { "name": frm.doc.bank_account }, ["account", "default_sun_cost_center"], function (value) {
				frm.set_value("payment_account", value.account);
				frm.set_value("sun_cost_center", value.default_sun_cost_center);
				frappe.db.get_value("Account", { "name": value.account }, "account_currency", function (value2) {
					frm.set_value("currency", value2.account_currency);
					frappe.db.get_value("Company", { "name": frm.doc.company }, "default_currency", function (value3) {
						if (value2.account_currency != value3.default_currency) {
							frm.set_df_property('conversion_rate', 'hidden', 0);
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
						} else {
							frm.set_value("conversion_rate", 1);
							frm.set_df_property('conversion_rate', 'hidden', 1);
						}
					});
				});

			});
		}
		else if (frm.doc.type == 'Employee') {
			frm.set_value("mode_of_payment", '');
			frm.set_value("bank_account", '');
			frm.set_value("payment_account", '');
			frm.set_value('supplier', '')
			frm.set_value('supplier_name', '')
			frappe.db.get_value("Company", { "name": frm.doc.company }, "default_employee_payable_account_mc_pav", function (value) {
				if (value.default_employee_payable_account_mc_pav) {
					frm.set_value("payment_account", value.default_employee_payable_account_mc_pav);
				} else {
					frappe.msgprint(__("Please Set Default Employee Payable Account MC PAV in the Company"));
				}
			});
		} else if (frm.doc.type == 'Supplier' && frm.doc.supplier) {
			frm.set_value("mode_of_payment", '');
			frm.set_value("employee", '');
			frm.set_value("payment_account", '');
			frm.set_value('employee_name', '')
			frappe.db.get_value("Supplier", { "name": frm.doc.supplier }, "default_currency", function (value) {
				if (value.default_currency) {
					frm.set_value("currency", value.default_currency);
				} else {
					frm.set_value("currency", '');
					frappe.msgprint(__("Please Set Billing Currency for Supplier"));
				}
			});
			frappe.call({
				method: "pav.pav.doctype.expense_entry_mc.expense_entry_mc.get_party_account_",
				args: {
					"supplier": frm.doc.supplier,
					"company": frm.doc.company
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value("payment_account", r.message.account);
					}
				}
			})

		} else {
			frm.set_value("payment_account", '');
		}
		frm.refresh_fields();
	},
	posting_date: function (frm) {
		frm.trigger("currency")
	},
	currency: function (frm) {
		if (frm.doc.currency && frm.doc.posting_date) {
			console.log('hi')
			frappe.db.get_value("Company", { "name": frm.doc.company }, "default_currency", function (value) {
				if (frm.doc.currency != value.default_currency) {
					frm.set_df_property('conversion_rate', 'hidden', 0);
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
				} else {
					frm.set_value("conversion_rate", 1);
					frm.set_df_property('conversion_rate', 'hidden', 1);
				}
			});
		}
	},
	from_mode_of_payment: function (frm) {
		frm.trigger("check_to_account")
		if (frm.doc.from_mode_of_payment) {
			frappe.call({
				method: "pav.pav.doctype.advance_request_mc.advance_request_mc.get_payment_account",
				args: {
					"mode_of_payment": frm.doc.from_mode_of_payment,
					"company": frm.doc.company
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value("from_account", r.message.account);
						frm.set_value("from_bank_account", '');
						frappe.db.get_value("Account", { "name": r.message.account }, "account_currency", function (value) {
							if (value.account_currency != frm.doc.currency) {
								frappe.msgprint(__("From Account Currency should to be same of Payment Account Currency"));
								validated = false;
							}
						});
					}
				}
			});
		}
		frm.refresh_fields();
	},
	from_bank_account: function (frm) {
		frm.trigger("check_to_account")
		if (frm.doc.from_bank_account) {
			frappe.db.get_value("Bank Account", { "name": frm.doc.from_bank_account }, "account", function (value) {
				frm.set_value("from_account", value.account);
				frm.set_value("from_mode_of_payment", '');
				frappe.db.get_value("Account", { "name": value.account }, "account_currency", function (value2) {
					if (value2.account_currency != frm.doc.currency) {
						frappe.msgprint(__("From Account Currency should to be same of Payment Account Currency"));
						validated = false;
					}
				});

			});
		}
		frm.refresh_fields();
	},


});
