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
from frappe.utils.csvutils import getlink
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.party import get_party_account
from frappe.utils import get_fullname, flt, cstr

class InvalidExpenseApproverError(frappe.ValidationError): pass
class ExpenseApproverIdentityError(frappe.ValidationError): pass

class AdvanceRequest(AccountsController):
	def validate(self):
		self.validate_amount()		
		self.amount_in_words=money_in_words(self.amount, self.currency)

	def on_submit(self):		
		self.validate_amount()		
		self.validate_accounts()
		self.make_gl_entries(cancel=False)
		if self.is_return:
			self.status='Return'
		else:
			self.status='Paid'
	
	def on_update(self):
		self.amount_in_words=money_in_words(self.amount, self.currency)

	def on_cancel(self):
		self.make_gl_entries(cancel=True)
		self.status=='Cancelled'

	def validate_amount(self):
		if frappe.db.get_value("Company",{"name": self.company}, "default_currency")==self.currency:
			self.base_amount=self.amount
			self.conversion_rate=1
		else:
			self.base_amount=self.amount*self.conversion_rate
	
	def validate_status(self):
		if self.status not in ('Approved','Rejected'):
			frappe.throw(_("""Status Must to be Approved or Rejected"""))

	def validate_accounts(self):
		if not self.account:
			frappe.throw(_("""Account is Mandatory"""))
		if not self.from_account:
			frappe.throw(_("""From Account is Mandatory"""))
		account_currency=frappe.db.get_value("Account", { "name": self.from_account }, "account_currency")
		if account_currency!=self.currency:
			frappe.throw(_("From Account Currency should to be same of Account Currency"))
		
	def make_gl_entries(self, cancel=False):
		if self.amount<=0:
			frappe.throw(_("""Amount Must be < 0"""))
		gl_entries = self.get_gl_entries()
		make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		party_type=''
		party=''
		if self.type=='Employee Account':
			party_type=self.type
		if self.employee_account:
			party=self.employee_account
		gl_entry = []
		if self.is_return:
			gl_entry.append(
				self.get_gl_dict({
					"posting_date": self.posting_date,
					"account": self.account,
					"account_currency": self.currency,
					"credit": self.base_amount,
					"credit_in_account_currency": self.amount,
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
					"debit": self.base_amount,
					"debit_in_account_currency": self.amount,
					"conversion_rate":self.conversion_rate,
					"against": self.account,
					"remarks": self.user_remark,
					"cost_center": self.cost_center
				}, item=self)
			)
		else:			
			gl_entry.append(
				self.get_gl_dict({
					"posting_date": self.posting_date,
					"account": self.account,
					"account_currency": self.currency,
					"debit": self.base_amount,
					"debit_in_account_currency": self.amount,
					"conversion_rate":self.conversion_rate,
					"against": self.from_account,
					"party_type": party_type,
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
					"against": self.account,
					"remarks": self.user_remark,
					"cost_center": self.cost_center
				}, item=self)
			)
		return gl_entry

