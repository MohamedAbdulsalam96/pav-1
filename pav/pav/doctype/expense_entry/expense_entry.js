// Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt


frappe.provide("pav.pav");

pav.pav.ExpenseEntryController = frappe.ui.form.Controller.extend({
    amount: function (doc, cdt, cdn) {
        var child = locals[cdt][cdn];
        if (!child.default_account || !child.account_currency) {
            frappe.msgprint(__("Please set the Expense Type First"));
            return;
        } else if (!doc.company || !doc.default_currency) {
            frappe.msgprint(__("Please set the Company First"));
            return;
        } else {
            console.log("child.account_currency=" + child.account_currency)
            console.log("doc.currency=" + doc.currency)
            console.log("doc.default_currency=" + doc.default_currency)
            //frappe.model.set_value(cdt, cdn, 'account_amount', child.amount * (child.account_currency==doc.currency?1:doc.conversion_rate));
            //frappe.model.set_value(cdt, cdn, 'base_amount', (child.amount * (child.account_currency==doc.currency?1:doc.conversion_rate)) * (child.account_currency==doc.default_account?1:1/doc.conversion_rate));
            frappe.model.set_value(cdt, cdn, 'account_amount',
                child.amount * (child.account_currency == doc.currency ? 1 : doc.conversion_rate));
            frappe.model.set_value(cdt, cdn, 'base_amount',
                child.account_currency == doc.default_currency ?
                    (child.amount * (child.account_currency == doc.currency ? 1 : doc.conversion_rate)) :
                    (child.amount * (child.account_currency == doc.currency ? 1 : doc.conversion_rate)) * (doc.conversion_rate))
        }
    },

    expense_type: function (doc, cdt, cdn) {
        var d = locals[cdt][cdn];
        if (!doc.company) {
            frappe.msgprint(__("Please set the Company"));
            this.frm.refresh_fields();
            return;
        }

        if (!d.expense_type) {
            return;
        }

        return frappe.call({
            method: "pav.pav.doctype.expense_entry.expense_entry.get_expense_entry_account",
            args: {
                "expense_claim_type": d.expense_type,
                "company": doc.company
            },
            callback: function (r) {
                if (r.message) {
                    console.log("doc.currency=" + doc.currency)
                    console.log("doc.default_currency=" + doc.default_currency)
                    console.log("r.message.account_currency=" + r.message.account_currency)
                    d.default_account = r.message.account;
                    d.account_currency = r.message.account_currency;
                    if (doc.currency != r.message.account_currency && doc.default_currency != r.message.account_currency) {
                        frappe.msgprint(__("Expense Currency must to be equal Payment Currency or Company Currency"));
                    }
                }
            }
        });
        cur_frm.refresh_field('expenses');

    }
});

$.extend(cur_frm.cscript, new pav.pav.ExpenseEntryController({
    frm: cur_frm
}));

cur_frm.add_fetch('expense_type', 'description', 'description');

cur_frm.cscript.onload = function (doc) {
    if (doc.__islocal) {
        cur_frm.set_value("posting_date", frappe.datetime.get_today());
        //cur_frm.cscript.clear_sanctioned(doc);
    }
};

cur_frm.cscript.set_help = function (doc) {
    cur_frm.set_intro("");
    if (doc.__islocal && !in_list(frappe.user_roles, "HR User")) {
        cur_frm.set_intro(__("Fill the form and save it"));
    }
};

cur_frm.cscript.validate = function (doc) {
    $.each(doc.expenses || [], function (i, d) {
        if (doc.currency != d.account_currency && doc.default_currency != d.account_currency) {
            frappe.throw(__("Expense Currency must to be equal Payment Currency or Company Currency in Row " + (i + 1)));
        }

        //d.base_amount = d.amount * doc.conversion_rate
        d.account_amount = d.amount * (d.account_currency == doc.currency ? 1 : doc.conversion_rate)
        d.base_amount = d.account_currency == doc.default_currency ?
            (d.amount * (d.account_currency == doc.currency ? 1 : doc.conversion_rate)) :
            (d.amount * (d.account_currency == doc.currency ? 1 : doc.conversion_rate)) * (doc.conversion_rate)

        if (!d.cost_center) {
            if (doc.cost_center) {
                d.cost_center = doc.cost_center
            }
            else {
                frappe.throw(__("Please set Cost Center"));
            }

        }
        if (!d.project) {
            if (doc.project) {
                d.project = doc.project
            }
        }

    });
    cur_frm.refresh_field('expenses');
    cur_frm.cscript.calculate_total(doc);
};

cur_frm.cscript.calculate_total = function (doc) {
    doc.total_amount = 0;
    doc.base_total_amount = 0;

    $.each((doc.expenses || []), function (i, d) {
        doc.total_amount += d.amount;
        doc.base_total_amount += d.base_amount;
    });
};

erpnext.expense_claim = {
    set_title: function (frm) {
        if (!frm.doc.task) {
            frm.set_value("title", "Test Title");
        } else {
            frm.set_value("title", "Test Title" + " for " + frm.doc.task);
        }
    }
};

cur_frm.fields_dict['task'].get_query = function (doc) {
    return {
        filters: {
            'project': doc.project
        }
    };
};

frappe.ui.form.on("Expense Entry", {
    setup: function (frm) {
        frm.trigger("set_query_for_cost_center");
        frm.add_fetch("company", "cost_center", "cost_center");
        frm.set_df_property('myfield',  'hidden',  (frm.doc.currency == frm.doc.default_currency) ? 1 : 0);        
    },

    onload: function (frm) { },

    refresh: function (frm) {
        //frm.trigger("toggle_fields");

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
    },

    set_query_for_cost_center: function (frm) {
        frm.fields_dict["cost_center"].get_query = function () {
            return {
                filters: {
                    "company": frm.doc.company,
                    "is_group": 0
                }
            };
        };
    },
    payment_account: function (frm) {

    },
    currency: function (frm) {
        if (frm.doc.currency == frm.doc.default_currency) {
            frm.set_value("conversion_rate", 1);
            frm.set_df_property('conversion_rate',  'hidden', 1);        
        } else if (frm.doc.conversion_rate == 1 && frm.doc.currency != frm.doc.default_currency) {
            frm.set_df_property('conversion_rate',  'hidden', 0);        
            frappe.call({
                method: "erpnext.setup.utils.get_exchange_rate",
                args: {
                    from_currency: frm.doc.currency,
                    to_currency: frm.doc.default_currency,
                    transaction_date: frm.doc.posting_date
                },
                callback: function (r, rt) {
                    frm.set_value("conversion_rate", r.message);
                }
            })
        }
    },
    type: function (frm) {
        frm.set_value("party", "");
        frm.set_value("payment_account", "");
        frm.set_value("currency", "");       
    },
    party: function (frm) {
        if (!frm.doc.default_currency) {
            frm.set_value("party", "");
            frm.set_value("payment_account", "");
            frm.set_value("currency", "");
            frappe.msgprint(__("Please set Currency Company First"));
            this.frm.refresh_fields();
            return;
        }
        else if (frm.doc.party && frm.doc.type=='Mode of Payment') {            
            frappe.call({
                method: "pav.pav.doctype.expense_entry.expense_entry.get_payment_account",
                args: {
                    "mode_of_payment": frm.doc.party,
                    "company": frm.doc.company
                },
                callback: function (r) {
                    if (r.message) {
                        cur_frm.set_value("payment_account", r.message.account);
                        frm.refresh_fields();
                        cur_frm.refresh_field('currency');
                    } else {
                        console.log("yyyyyyyy")
                        frm.set_value("payment_account", "");
                        frm.set_value("party", "");
                        frm.refresh_fields();
                        return;
                    }
                }
            });
            console.log(frm.doc.payment_account)
        }
        else if (frm.doc.party && frm.doc.type=='Bank Account') {
            frappe.db.get_value("Bank Account", {"name": frm.doc.party}, "account", function(value) {
                if(value.account){
                    frm.set_value("payment_account", value.account);
                    cur_frm.refresh_field('payment_account');
                }else{
                    console.log("yyyyyyyy")
                    frm.set_value("payment_account", "");
                    frm.set_value("party", "");
                    frm.refresh_fields();
                    return;
                }                
            })
        }
        else if (frm.doc.party && frm.doc.type=='Employee Account') {
            frappe.db.get_value("Company", {"name": frm.doc.company}, "default_employee_payable_account_mc_pav", function(value) {
				if (value.default_employee_payable_account_mc_pav){
                    frappe.db.get_value("Employee Account", {"name": frm.doc.party}, "currency", function(emp_acc) {
                        frappe.db.get_value("Account", {"parent_account": value.default_employee_payable_account_mc_pav,
                                                    "account_currency":emp_acc.currency}, "name", function(acc) {
                            frm.set_value("payment_account", acc.name);
                            cur_frm.refresh_field('payment_account');
                        });
                    });                    					
				}else{
					frappe.msgprint(__("Please Set Default Employee Payable Account MC PAV in the Company"));
				}
            });
            
        }
    }

});