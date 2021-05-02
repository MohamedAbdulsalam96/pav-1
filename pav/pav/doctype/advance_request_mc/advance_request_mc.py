# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, money_in_words, nowdate
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController

class InvalidExpenseApproverError(frappe.ValidationError): pass
class ExpenseApproverIdentityError(frappe.ValidationError): pass

class AdvanceRequestMC(AccountsController):
	def validate(self):
		self.validate_amount()
		self.validate_employee()
		self.amount_in_words=money_in_words(self.amount, self.currency)

	def on_submit(self):
		self.validate_accounts()
		self.validate_amount()
		self.validate_status()
	
	def on_update(self):
		self.amount_in_words=money_in_words(self.amount, self.currency)

	def on_cancel(self):
		self.make_gl_entries(cancel=True)					
		self.status=='Cancelled'

	def make_gl_entries(self, cancel=False):
		if self.amount<=0:
			frappe.throw(_("""Amount Must be < 0"""))
		gl_entries = self.get_gl_entries()
		make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		gl_entry = []
		if self.is_return:
			gl_entry.append(
				self.get_gl_dict({
					"posting_date": self.posting_date,
					"account": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
					"account_currency": self.currency,
					"credit": self.base_amount,
					"credit_in_account_currency": self.amount,
					"conversion_rate":self.conversion_rate,
					"against": self.from_account,
					"party_type": '' if self.type!='Employee' else 'Employee Account',
					"party": '' if self.type!='Employee' else frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name"),
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
					"debit": self.base_amount,
					"debit_in_account_currency": self.amount,
					"conversion_rate":self.conversion_rate,
					"against": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
					"remarks": self.user_remark,
					"cost_center": self.cost_center
				}, item=self)
			)
		else:
			party_type=''
			party=''			
			if self.type=='Employee':
				party_type=='Employee Account'
				party=frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name")
			elif self.type=='Supplier':
				frappe.msgprint("test")
				party_type==self.type
				##frappe.msgprint("{0}".format(self.type))
				##frappe.msgprint("party_type={0}".format(party_type))
				party=self.supplier
			##frappe.msgprint("{0}-{1}".format(party_type,party))
			##frappe.msgprint("{0}-{1}".format(self.type,self.supplier))
			##frappe.msgprint("{0}".format(self))
			gl_entry.append(
				self.get_gl_dict({
					"posting_date": self.posting_date,
					"account": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
					"account_currency": self.currency,
					"debit": self.base_amount,
					"debit_in_account_currency": self.amount,
					"conversion_rate":self.conversion_rate,
					"against": self.from_account,
					"party_type": 'Supplier' if self.type=='Supplier' else ('Employee Account' if self.type=='Employee' else ''),
					"party": party ,
					"remarks": self.user_remark,
					"cost_center": self.cost_center
				}, item=self)
			)
			gl_entry.append(
				self.get_gl_dict({
					"posting_date": self.posting_date,
					"account": self.from_account,
					"account_currency": self.currency,
					"credit": self.base_amount,
					"credit_in_account_currency": self.amount,
					"conversion_rate":self.conversion_rate,
					"against": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
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
		##
		if self.is_return:
			accounts.append({				
				"account": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
				"account_currency": self.currency,
				"credit": self.base_amount,
				"credit_in_account_currency": self.amount,
				"conversion_rate":self.conversion_rate,
				"against": self.from_account,
				"party_type": '' if self.type!='Employee' else 'Employee Account',
				"party": '' if self.type!='Employee' else frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name"),
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
				"debit": self.base_amount,
				"debit_in_account_currency": self.amount,
				"conversion_rate":self.conversion_rate,
				"against": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
				"remarks": self.user_remark,
				"cost_center": self.cost_center,
				"reference_type":self.doctype,
				"reference_name":self.name
			})
		else:
			party_type=''
			party=''			
			if self.type=='Employee':
				party_type=='Employee Account'
				party=frappe.db.get_value("Employee Account",{"employee": self.employee,"currency":self.currency}, "name")
			elif self.type=='Supplier':
				frappe.msgprint("test")
				party_type==self.type
				party=self.supplier
			accounts.append({				
				"account": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
				"account_currency": self.currency,
				"debit": self.base_amount,
				"debit_in_account_currency": self.amount,
				"conversion_rate":self.conversion_rate,
				"against": self.from_account,
				"party_type": 'Supplier' if self.type=='Supplier' else ('Employee Account' if self.type=='Employee' else ''),
				"party": party ,
				"remarks": self.user_remark,
				"cost_center": self.cost_center,
				"reference_type":self.doctype,
				"reference_name":self.name
			})
			accounts.append({				
				"account": self.from_account,
				"account_currency": self.currency,
				"credit": self.base_amount,
				"credit_in_account_currency": self.amount,
				"conversion_rate":self.conversion_rate,
				"against": self.payment_account if self.type!='Employee' else frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name"),
				"remarks": self.user_remark,
				"cost_center": self.cost_center,
				"reference_type":self.doctype,
				"reference_name":self.name
			})
		##
		journal_entry.set("accounts", accounts)
		journal_entry.title = self.purpose
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
		if not self.from_account:
			frappe.throw(_("""From Account is Mandatory"""))
		if self.type!='Employee':
			self.currency=frappe.db.get_value("Account",{"name": self.payment_account}, "account_currency")
			from_account_currency = frappe.db.get_value("Account",{"name": self.from_account}, "account_currency")
			if self.currency!=from_account_currency:
				frappe.throw(_("""From Account Must be Same Currency"""))
		else:
			if not self.employee:
				frappe.throw(_("""Employee is Mandatory"""))
			paypal_account=frappe.db.get_value("Account",{"parent_account": self.payment_account,"account_currency":self.currency}, "name")
			if not paypal_account:
				frappe.throw(_("""Payment Account Must to have Child with Mentioned Currency"""))			
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
			self.base_amount=self.amount
			self.conversion_rate=1
		else:
			self.base_amount=self.amount*self.conversion_rate

	def validate_status(self):
		if self.status not in ('Approved','Rejected'):
			frappe.throw(_("""Status Must to be Approved or Rejected"""))


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
