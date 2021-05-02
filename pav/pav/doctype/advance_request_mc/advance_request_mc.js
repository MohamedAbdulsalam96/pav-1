// Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Advance Request MC', {
	refresh: function (frm) {
		frm.set_df_property('currency', 'read_only', frm.doc.type == 'Employee' ? 0 : 1);
		if (!frm.is_new()) {
			frappe.db.get_value("Company", { "name": frm.doc.company }, "default_currency", function (value) {
				frm.set_df_property('conversion_rate', 'hidden', value.default_currency == frm.doc.currency ? 1 : 0);
				frm.set_df_property('base_amount', 'hidden', value.default_currency == frm.doc.currency ? 1 : 0);
			});
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
		frm.set_df_property('currency', 'read_only', frm.doc.type == 'Employee' ? 0 : 1);
		frm.trigger("fill_to_account")
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
		frm.set_df_property('currency', 'read_only', frm.doc.type == 'Employee' ? 0 : 1);
		if (!frm.doc.company) {
			frappe.msgprint(__("Please Set the Company First"));
			frm.refresh_fields();
			return;
		}
		if (frm.doc.type == 'Mode of Payment' && frm.doc.mode_of_payment) {
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
						}
					});

				});

			});
		}
		else if (frm.doc.type == 'Employee') {
			frm.set_value("mode_of_payment", '');
			frm.set_value("bank_account", '');
			frm.set_value("payment_account", '');
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
	currency: function (frm) {
		if (frm.doc.currency) {
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
				}
			});
		}
	},
});
