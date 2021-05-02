# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, money_in_words, nowdate
from frappe.model.document import Document
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.party import get_party_account
from erpnext.controllers.accounts_controller import AccountsController

class InvalidExpenseApproverError(frappe.ValidationError): pass
class ExpenseApproverIdentityError(frappe.ValidationError): pass

class ExpenseEntryMC(AccountsController):
	def validate(self):
		self.validate_amount()
		self.validate_employee()
		self.validate_detail()
		self.validate_payment()

	def on_submit(self):
		self.validate_accounts()
		self.validate_amount()
		self.validate_status()
		#if self.status=='Approved':
		#	self.make_gl_entries()
		#if not self.currency:
		#	frappe.throw(_("""Currency is Mandatory"""))

	def on_cancel(self):
		#self.make_gl_entries(cancel=True)
		self.status=='Cancelled'

	def make_gl_entries(self, cancel=False):
		if self.amount<=0 or self.base_amount<=0:
			frappe.throw(_("""Amount and Base Amount Must be < 0"""))
		gl_entries = self.get_gl_entries()
		make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		gl_entry = []
		against_acc = []
		party=None
		party_type=None
		account=self.payment_account
		if self.type=='Employee':
			party=frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name")
			party_type='Employee Account'
			account=frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name")
		elif self.type=='Supplier':
			party=self.supplier
			party_type='Supplier'
		
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
							"against": account,
							"cost_center": data.cost_center,
							"project": data.project,
							"remarks": data.description
						}, item=data))
				else:frappe.throw(_("""{0} Account Must to have Child with {1} Currency""").format(expense_account_p,self.currency))
			else:frappe.throw(_("""Account of {0} Expense Type is Missing""").format(data.expense_type))
		gl_entry.append(
			self.get_gl_dict({
				"posting_date": self.posting_date,
				"account": account,
				"account_currency": self.currency,
				"credit": self.base_amount,
				"credit_in_account_currency": self.amount,
				"conversion_rate":self.conversion_rate,
				"against": ','.join(against_acc),
				"party_type": party_type,
				"party": party,
				"cost_center": self.cost_center,
				"project": self.project,
				"against_voucher_type": self.doctype,
				"against_voucher": self.name,
				"remarks": self.user_remark
			}, item=self)
		)
		if self.is_paid and (self.type=='Employee' or self.type=='Supplier'):
			gl_entry.append(
				self.get_gl_dict({
					"posting_date": self.posting_date,
					"account": account,
					"account_currency": self.currency,
					"debit": self.paid_base_amount,
					"debit_in_account_currency": self.paid_amount,
					"conversion_rate":self.conversion_rate,
					"against": self.from_account,
					"party_type": party_type,
					"party": party,
					"against_voucher_type": self.doctype,
					"against_voucher": self.name,
					"remarks": self.user_remark,
					"cost_center": self.cost_center
				}, item=self)
			)
			gl_entry.append(
				self.get_gl_dict({
					"posting_date": self.posting_date,
					"account": self.from_account,
					"account_currency": self.currency,
					"credit": self.paid_base_amount,
					"credit_in_account_currency": self.paid_amount,
					"conversion_rate":self.conversion_rate,
					"against": party,
					"remarks": self.user_remark,
					"cost_center": self.cost_center
				}, item=self)
			)
		return gl_entry

	def make_accrual_jv_entry(self):
		journal_entry = frappe.new_doc('Journal Entry')
		
		journal_entry.voucher_type = 'Journal Entry'
		journal_entry.user_remark = self.user_remark		
		journal_entry.cheque_date = self.posting_date
		journal_entry.cheque_no = self.name
		journal_entry.company = self.company
		journal_entry.posting_date = nowdate()
		journal_entry.multi_currency=1
		accounts = []

		against_acc = []
		party=None
		party_type=None
		account=self.payment_account
		if self.type=='Employee':
			party=frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name")
			party_type='Employee Account'
			account=frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name")
		elif self.type=='Supplier':
			party=self.supplier
			party_type='Supplier'
		
		for data in self.expenses:
			expense_account_p=frappe.db.get_value("Expense Type Account MC",{"parent": data.expense_type,"company":self.company}, "default_account")
			if expense_account_p:
				expense_account=frappe.db.get_value("Account",{"parent_account": expense_account_p,"account_currency":self.currency}, "name")
				if expense_account:
					if expense_account not in against_acc:
						against_acc.append(expense_account)
					accounts.append({				
						"account": expense_account,
						"account_currency": self.currency,
						"debit": data.base_amount,
						"debit_in_account_currency": data.amount,
						"conversion_rate":self.conversion_rate,
						"against": account,
						"cost_center": data.cost_center,
						"project": data.project,
						"remarks": data.description,
						"reference_type":self.doctype,
						"reference_name":self.name
					})
				else:frappe.throw(_("""{0} Account Must to have Child with {1} Currency""").format(expense_account_p,self.currency))
			else:frappe.throw(_("""Account of {0} Expense Type is Missing""").format(data.expense_type))
		accounts.append({				
			"account": account,
			"account_currency": self.currency,
			"credit": self.base_amount,
			"credit_in_account_currency": self.amount,
			"conversion_rate":self.conversion_rate,
			"against": ','.join(against_acc),
			"party_type": party_type,
			"party": party,
			"cost_center": self.cost_center,
			"project": self.project,
			"against_voucher_type": self.doctype,
			"against_voucher": self.name,
			"remarks": self.user_remark,
			"reference_type":self.doctype,
			"reference_name":self.name
		})
		if self.is_paid and (self.type=='Employee' or self.type=='Supplier'):
			accounts.append({				
				"account": account,
				"account_currency": self.currency,
				"debit": self.paid_base_amount,
				"debit_in_account_currency": self.paid_amount,
				"conversion_rate":self.conversion_rate,
				"against": self.from_account,
				"party_type": party_type,
				"party": party,
				"against_voucher_type": self.doctype,
				"against_voucher": self.name,
				"remarks": self.user_remark,
				"cost_center": self.cost_center,
				"reference_type":self.doctype,
				"reference_name":self.name
			})
			accounts.append({				
				"account": self.from_account,
				"account_currency": self.currency,
				"credit": self.paid_base_amount,
				"credit_in_account_currency": self.paid_amount,
				"conversion_rate":self.conversion_rate,
				"against": party,
				"remarks": self.user_remark,
				"cost_center": self.cost_center,
				"reference_type":self.doctype,
				"reference_name":self.name
			})
		##
		
		
		##
		journal_entry.set("accounts", accounts)
		journal_entry.title = self.title
		try:
			journal_entry.save()
		except Exception as e:
			frappe.msgprint(e)
				
		self.jv_created=1
		self.save()
		frappe.msgprint(_("Journal Entry Created for Currenct Document {0} ")
			.format(journal_entry.name))
		
		self.reload()
		return journal_entry
	
	def validate_accounts(self):
		if not self.payment_account:
			frappe.throw(_("""Payment Account is Mandatory"""))
		if self.type!='Employee':
			self.currency=frappe.db.get_value("Account",{"name": self.payment_account}, "account_currency")
		elif self.type!='Supplier':
			if not self.employee:
				frappe.throw(_("""Employee is Mandatory"""))
			paypal_account=frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name")
			if not paypal_account:
				frappe.throw(_("""{0} Account Must to have Child with {1} Currency""").format(self.payment_account,self.currency))			
			employee_account=frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name")
			if not employee_account:
				#ea = frappe.new_doc('Employee Account')
				frappe.get_doc({
					'doctype': 'Employee Account',					
					'employee': self.employee,
					'currency': self.currency
				}).insert(ignore_permissions=True)
				#ea.employee=self.employee
				#ea.currency=self.currency
				#ea.save()
		else:
			if not self.supplier:
				frappe.throw(_("""Supplier is Mandatory"""))

	def validate_employee(self):
		if self.type=='Employee':
			employee_account=frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name")
			if not employee_account:
				frappe.get_doc({
					'doctype': 'Employee Account',					
					'employee': self.employee,
					'currency': self.currency
				}).insert(ignore_permissions=True)
				#ea = frappe.new_doc('Employee Account')
				#ea.employee=self.employee
				#ea.currency=self.currency
				#ea.save()


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
	
	def validate_payment(self):
		if self.from_account:
			from_account_currency=frappe.db.get_value("Account",{"name": self.from_account}, "account_currency")
			if from_account_currency!=self.currency:
				frappe.throw(_("""Currency of From Account Must to be Same Transaction Currency"""))
		if self.same_amount:
			self.paid_amount=self.amount
		self.paid_base_amount=self.amount*self.conversion_rate
		self.paid_amount_in_words=money_in_words(self.paid_amount, self.currency)


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

@frappe.whitelist()
def get_party_account_(supplier, company):
	account = get_party_account("Supplier", supplier, company)
	return {
		"account": account
	}
