# -*- coding: utf-8 -*-
# Copyright (c) 2021, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe import scrub
from frappe.utils import cstr
from frappe.model.document import Document
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

class GLEntryCurrency(Document):
	def validate(self):		
		exists = frappe.db.get_value("GL Entry Currency", {'currency': self.currency}, ['name'])

		if exists and self.is_new():
			frappe.throw("Currency already used in GL Entry")

	def after_insert(self):
		make_currency_in_gl_entry(cstr(self.currency))
		make_currency_in_budget_account(cstr(self.currency))
	
	def on_trash(self):
		delete_currency_from_gl_entry(cstr(self.currency))
		delete_currency_from_budget_account(cstr(self.currency))

def make_currency_in_gl_entry(currency):
	df = {
		"fieldname": scrub(currency),
		"label": currency,
		"fieldtype": "Link",
		"options": "Currency",	
		"insert_after": "credit_in_account_currency",
		"default":currency,
		"owner": "Administrator"
	}
	create_custom_field("GL Entry", df)
	df = {
		"fieldname": "debit_in_"+scrub(currency),
		"label": "Debit in "+currency,
		"fieldtype": "Currency",
		"options": scrub(currency),
		"insert_after": scrub(currency),
		"default":"0",
		"owner": "Administrator"
	}
	create_custom_field("GL Entry", df)
	df = {
		"fieldname": "credit_in_"+scrub(currency),
		"label": "Credit in "+currency,
		"fieldtype": "Currency",
		"options": scrub(currency),
		"insert_after": "debit_in_"+scrub(currency),
		"default":"0",
		"owner": "Administrator"
	}
	create_custom_field("GL Entry", df)
	frappe.clear_cache(doctype="GL Entry")

def make_currency_in_budget_account(currency):
	df = {
		"fieldname": "budget_amount_in_"+scrub(currency),
		"label": "Budget Amount in "+currency,
		"fieldtype": "Currency",		
		"insert_after": "budget_amount",
		"default":"0",
		"owner": "Administrator"
	}
	create_custom_field("Budget Account", df)	
	frappe.clear_cache(doctype="Budget Account")

def delete_currency_from_gl_entry(currency):
	doclist = [scrub(currency),"debit_in_"+scrub(currency),"credit_in_"+scrub(currency)]

	frappe.db.sql("""
		DELETE FROM `tabCustom Field`
		WHERE fieldname IN (%s)
		AND dt = 'GL Entry'""" %			#nosec
		(', '.join(['%s']* len(doclist))), tuple(doclist))

	frappe.db.sql("""
		DELETE FROM `tabProperty Setter`
		WHERE field_name IN (%s)
		AND doc_type = 'GL Entry'""" %		#nosec
		(', '.join(['%s']* len(doclist))), tuple(doclist))

	frappe.clear_cache(doctype="GL Entry")

def delete_currency_from_budget_account(currency):
	doclist = ["budget_amount_in_"+scrub(currency)]

	frappe.db.sql("""
		DELETE FROM `tabCustom Field`
		WHERE fieldname IN (%s)
		AND dt = 'Budget Account'""" %			#nosec
		(', '.join(['%s']* len(doclist))), tuple(doclist))

	frappe.db.sql("""
		DELETE FROM `tabProperty Setter`
		WHERE field_name IN (%s)
		AND doc_type = 'Budget Account'""" %		#nosec
		(', '.join(['%s']* len(doclist))), tuple(doclist))

	frappe.clear_cache(doctype="Budget Account")