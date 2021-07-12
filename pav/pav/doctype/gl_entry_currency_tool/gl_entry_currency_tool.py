# -*- coding: utf-8 -*-
# Copyright (c) 2021, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.setup.utils import get_exchange_rate
from erpnext import get_company_currency
from frappe import scrub
from frappe.utils.background_jobs import enqueue

class GLEntryCurrencyTool(Document):
	def update_gl_entry(self):
		frappe.enqueue(update_gl_entry_enqueue, doc=self)
		
def get_gl_entry(doc):
	return frappe.db.sql("""
		select * from `tabGL Entry`
		where company = %s and posting_date between %s and %s
	""" % ('%s', '%s', '%s'), (doc.company,doc.from_date,doc.to_date), as_dict=1)

def update_gl_entry_enqueue(doc):	
	cc=get_company_currency(doc.company)
	currs = frappe.get_all("GL Entry Currency", fields=["currency"])
	if currs:
		entries=get_gl_entry(doc=doc)
		if entries:
			for entry in entries:
				update_statments = []				
				for curr in currs:
					de,cr=0,0
					if curr.currency==cc:
						de,cr=entry.debit,entry.credit
					elif curr.currency==entry.account_currency:
						de,cr=entry.debit_in_account_currency,entry.credit_in_account_currency
					else:
						creur=1/get_exchange_rate(curr.currency,cc,entry.posting_date)
						de=(1 if not creur else creur)*entry.debit
						cr=(1 if not creur else creur)*entry.credit
					update_statments.append(""" %s = %s , debit_in_%s = %s , credit_in_%s = %s """ % (scrub(curr.currency),curr.currency,scrub(curr.currency),de,scrub(curr.currency),cr))
				update_statment= " {}".format(" , ".join(update_statments)) if update_statments else ""
				frappe.db.sql("""update `tabGL Entry`
					set %s
					where name='%s'""" % (update_statment,entry.name))
				
		else:
			frappe.throw(_("There is no GL Entry"))
	else:
		frappe.throw(_("There is no Curreny"))