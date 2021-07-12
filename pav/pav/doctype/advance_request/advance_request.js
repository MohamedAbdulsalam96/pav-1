// Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Advance Request', {
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
	setup: function (frm) {
	},
	refresh: function (frm) {
		if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Accounting Ledger'), function () {
                frappe.route_options = {
                    "voucher_no": frm.doc.name,
                    "from_date": frm.doc.posting_date,
                    "to_date": frm.doc.posting_date,
                    "company": frm.doc.company
                };
                frappe.set_route("query-report", "General Ledger");
            }, __("View"));
        }
		if (!frm.is_new()) {
			frappe.db.get_value("Company", { "name": frm.doc.company }, "default_currency", function (value) {
				frm.set_df_property('conversion_rate', 'hidden', value.default_currency == frm.doc.currency ? 1 : 0);
				frm.set_df_property('base_advance_amount', 'hidden', value.default_currency == frm.doc.currency ? 1 : 0);
			});
		}
		if (frm.doc.docstatus === 1
			&& (flt(frm.doc.paid_amount) < flt(frm.doc.advance_amount))
			&& frappe.model.can_create("Payment Entry")) {
			//			frm.add_custom_button(__('Payment'),
			//			function() { frm.events.make_payment_entry(frm); }, __('Create'));

			//
			frm.add_custom_button(__('Payment Entry'), function () {
				frappe.route_options = {
					"payment_type": "Internal Transfer",
					"paid_to": frm.doc.account,
					"advance_request": frm.doc.name,
					"mode_of_payment": frm.doc.mode_of_payment_from,
					"paid_amount": frm.doc.advance_amount,
					"base_paid_amount": frm.doc.advance_amount,
					"base_received_amount": frm.doc.advance_amount,
					"received_amount": frm.doc.advance_amount
				},
					frappe.set_route("Form", "Payment Entry", "New Payment Entry 1");
			}, __("Create"));
			//
		}
		else if (
			frm.doc.docstatus === 1
			&& flt(frm.doc.claimed_amount) < flt(frm.doc.paid_amount) - flt(frm.doc.return_amount)
			&& frappe.model.can_create("Expense Entry")
		) {
			frm.add_custom_button(
				__("Expense Entry"),
				function () {
					frm.events.make_expense_claim(frm);
				},
				__('Create')
			);
		}

		if (frm.doc.docstatus === 1
			&& (flt(frm.doc.claimed_amount) + flt(frm.doc.return_amount) < flt(frm.doc.paid_amount))
			&& frappe.model.can_create("Journal Entry")) {

			frm.add_custom_button(__("Return"), function () {
				frm.trigger('make_return_entry');
			}, __('Create'));
		}
	},

	make_payment_entry: function (frm) {
		var method = "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry";
		if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
			method = "pav.pav.doctype.advance_request.advance_request.make_bank_entry"
		}
		return frappe.call({
			method: method,
			args: {
				"dt": frm.doc.doctype,
				"dn": frm.doc.name
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		});
	},

	make_expense_claim: function (frm) {
		return frappe.call({
			method: "erpnext.hr.doctype.expense_claim.expense_claim.get_expense_claim",
			args: {
				"employee_name": frm.doc.employee,
				"company": frm.doc.company,
				"employee_advance_name": frm.doc.name,
				"posting_date": frm.doc.posting_date,
				"paid_amount": frm.doc.paid_amount,
				"claimed_amount": frm.doc.claimed_amount
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		});
	},

	make_return_entry: function (frm) {
		frappe.call({
			method: 'erpnext.hr.doctype.employee_advance.employee_advance.make_return_entry',
			args: {
				'employee': frm.doc.employee,
				'company': frm.doc.company,
				'employee_advance_name': frm.doc.name,
				'return_amount': flt(frm.doc.paid_amount - frm.doc.claimed_amount),
				'advance_account': frm.doc.advance_account,
				'mode_of_payment': frm.doc.mode_of_payment
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route('Form', doclist[0].doctype, doclist[0].name);
			}
		});
	},
	mode_of_payment: function (frm) {
		frappe.call({
			method: "pav.pav.doctype.expense_entry.expense_entry.get_payment_account",
			args: {
				"mode_of_payment": frm.doc.mode_of_payment,
				"company": frm.doc.company
			},
			callback: function (r) {
				if (r.message) {
					if (r.message.account) {
						cur_frm.set_value("account", r.message.account);
					}
					if (r.message.currency) {
						cur_frm.set_value("currency", r.message.currency);
					}
					frm.refresh_fields();
					cur_frm.refresh_field('account');

				} else {
					console.log("yyyyyyyy")
					frm.set_value("account", "");
					frm.set_value("currency", "");
					frm.set_value("mode_of_payment", "");
					frm.refresh_fields();
					return;
				}
				frm.refresh_fields();

			}
		});
		console.log(frm.doc.account)
	},
	fill_to_account: function (frm) {
		if (!frm.doc.company) {
			frappe.msgprint(__("Please Set the Company First"));
			frm.refresh_fields();
			return;
		}
		if (frm.doc.type == 'Mode of Payment' && frm.doc.mode_of_payment) {
			frm.set_value("bank_account", '');
			frm.set_value("employee_account", '');
			frm.set_value("account", '');
			if (frm.doc.mode_of_payment) {
				frappe.call({
					method: "pav.pav.doctype.advance_request_mc.advance_request_mc.get_payment_account",
					args: {
						"mode_of_payment": frm.doc.mode_of_payment,
						"company": frm.doc.company
					},
					callback: function (r) {
						if (r.message) {
							frm.set_value("account", r.message.account);
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
		}
		else if (frm.doc.type == 'Bank Account' && frm.doc.bank_account) {
			frm.set_value("mode_of_payment", '');
			frm.set_value("employee_account", '');
			frm.set_value("account", '');
			if (frm.doc.bank_account) {
				frappe.db.get_value("Bank Account", { "name": frm.doc.bank_account }, ["account"], function (value) {
					frm.set_value("account", value.account);
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
		}
		else if (frm.doc.type == 'Employee Account') {
			frm.set_value("mode_of_payment", '');
			frm.set_value("bank_account", '');
			frm.set_value("account", '');
			if (frm.doc.employee_account) {
				frappe.db.get_value("Employee Account", { "name": frm.doc.employee_account }, "currency", function (value5) {
					if (value5.currency) {
						//frm.set_value("currency", value.currency);
						//
						console.log("1")
						frappe.db.get_value("Company", { "name": frm.doc.company }, "default_employee_payable_account_mc_pav", function (value) {
							if (value.default_employee_payable_account_mc_pav) {
								//frm.set_value("account", value.default_employee_payable_account_mc_pav);
								//
								console.log("2")
								frappe.db.get_value("Account", { "parent_account": value.default_employee_payable_account_mc_pav, "account_currency": value5.currency }, "name", function (value2) {
									//console.log("2-2" + value2)
									if (value2.name) {
										console.log("3")
										frm.set_value("account", value2.name);
										frm.set_value("currency", value5.currency);
										frappe.db.get_value("Company", { "name": frm.doc.company }, "default_currency", function (value3) {
											if (value5.currency != value3.default_currency) {
												console.log("4")
												frm.set_df_property('conversion_rate', 'hidden', 0);
												frappe.call({
													method: "erpnext.setup.utils.get_exchange_rate",
													args: {
														from_currency: value5.currency,
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
									} else {
										frappe.msgprint(__("Please Create a Child Account for Default Employee Payable Account MC PAV in the Company"));
									}
								})
								//
							} else {
								frappe.msgprint(__("Please Set Default Employee Payable Account MC PAV in the Company"));
							}
						});
						//

					} else {
						frappe.msgprint(__("Please Set Currecy For Employee Account"));
					}
				});

			}

		} else {
			frm.set_value("account", '');
		}
		frm.refresh_fields();
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
	employee_account: function (frm) {
		frm.trigger("fill_to_account")
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
	/*
		employee: function (frm) {
			if (frm.doc.employee) {
				return frappe.call({
					method: "erpnext.hr.doctype.employee_advance.employee_advance.get_due_advance_amount",
					args: {
						"employee": frm.doc.employee,
						"posting_date": frm.doc.posting_date
					},
					callback: function(r) {
						frm.set_value("due_advance_amount",r.message);
					}
				});
			}
		}
	*/
});
