# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController

class InvalidExpenseApproverError(frappe.ValidationError): pass
class ExpenseApproverIdentityError(frappe.ValidationError): pass

class ExpenseEntryMC(AccountsController):
	def validate(self):
		self.validate_amount()
		self.validate_employee()
		self.validate_detail()

	def on_submit(self):
		self.validate_accounts()
		self.validate_amount()
		self.validate_status()
		if self.status=='Approved':
			self.make_gl_entries()

	def on_cancel(self):
		if self.status=='Approved':
			self.make_gl_entries(cancel=True)
		self.status=='Cancelled'

	def make_gl_entries(self, cancel=False):
		if self.amount<=0 or self.base_amount<=0:
			frappe.throw(_("""Amount and Base Amount Must be < 0"""))
		gl_entries = self.get_gl_entries()
		make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		gl_entry = []
		against_acc = []
		for data in self.expenses:
			expense_account_p=frappe.db.get_value("Expense Type Account MC",{"parent": data.expense_type,"company":self.company}, "default_account")
			if expense_account_p:
				expense_account=frappe.db.get_value("Account",{"parent_account": expense_account_p,"account_currency":self.currency}, "name")
				if expense_account:
					if expense_account not in against_acc:
						against_acc.append(expense_account)
					gl_entry.append(
						self.get_gl_dict({
							"posting_date": self.posting_date,
							"account": expense_account,
							"account_currency": self.currency,
							"debit": data.base_amount,
							"debit_in_account_currency": data.amount,
							"conversion_rate":self.conversion_rate,
							"against": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
							"cost_center": data.cost_center,
							"project": data.project,
							"against_voucher_type": self.doctype,
							"against_voucher": self.name,
							"remarks": data.description
						}, item=data))
				else:frappe.throw(_("""{0} Account Must to have Child with {1} Currency""").format(expense_account_p,self.currency))
			else:frappe.throw(_("""Account of {0} Expense Type is Missing""").format(data.expense_type))
		gl_entry.append(
			self.get_gl_dict({
				"posting_date": self.posting_date,
				"account": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
				"account_currency": self.currency,
				"credit": self.base_amount,
				"credit_in_account_currency": self.amount,
				"conversion_rate":self.conversion_rate,
				"against": ','.join(against_acc),
				"party_type": '' if self.type!='Employee' else 'Employee Account',
				"party": '' if self.type!='Employee' else frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name"),
				"cost_center": self.cost_center,
				"project": self.project,
				"against_voucher_type": self.doctype,
				"against_voucher": self.name,
				"remarks": self.user_remark
			}, item=self)
		)
		return gl_entry

	def validate_accounts(self):
		if not self.payment_account:
			frappe.throw(_("""Payment Account is Mandatory"""))
		if self.type!='Employee':
			self.currency=frappe.db.get_value("Account",{"name": self.payment_account}, "account_currency")
		else:
			if not self.employee:
				frappe.throw(_("""Employee is Mandatory"""))
			paypal_account=frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name")
			if not paypal_account:
				frappe.throw(_("""{0} Account Must to have Child with {1} Currency""").format(self.payment_account,self.currency))			
			employee_account=frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name")
			if not employee_account:
				ea = frappe.new_doc('Employee Account')
				ea.employee=self.employee
				ea.currency=self.currency
				ea.save()

	def validate_employee(self):
		if self.type=='Employee':
			employee_account=frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name")
			if not employee_account:
				ea = frappe.new_doc('Employee Account')
				ea.employee=self.employee
				ea.currency=self.currency
				ea.save()


	def validate_amount(self):
		if frappe.db.get_value("Company",{"name": self.company}, "default_currency")==self.currency:
			self.conversion_rate=1

	def validate_status(self):
		if self.status not in ('Approved','Rejected'):
			frappe.throw(_("""Status Must to be Approved or Rejected"""))

	def validate_detail(self):
		self.amount=0
		self.base_amount=0
		for data in self.expenses:
			self.amount+=data.amount
			self.base_amount+=data.amount*self.conversion_rate
			if not frappe.db.get_value("Expense Type Account MC",{"parent": data.expense_type,"company":self.company}, "default_account"):
				frappe.throw(_("""Account of {0} Expense Type is Missing""").format(data.expense_type))


@frappe.whitelist()
def get_payment_account(mode_of_payment, company):
	account = frappe.db.get_value("Mode of Payment Account",
		{"parent": mode_of_payment, "company": company}, "default_account")
	if not account:
		frappe.throw(_("Please set default account in Mode of Payment {0}")
			.format(mode_of_payment))

	return {
		"account": account,
		"account_currency": frappe.db.get_value("Account", {"name": account}, "account_currency")
	}
