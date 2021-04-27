# Copyright (c) 2013, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, formatdate

def execute(filters=None):
	if not filters:
		filters = {}
	columns, data = [], []
	columns = get_columns(filters)
	if filters.get("budget_against_filter"):
		dimensions = filters.get("budget_against_filter")
	else:
		dimensions = get_cost_centers(filters)
	
	dimension_target_details = get_dimension_target_details(dimensions,filters)	
	balances = get_opening_balances(dimensions,filters)	
	#frappe.msgprint("{0}".format(dimension_target_details))
	for ccd in dimension_target_details:
		if ccd.debit>ccd.credit:
			debit=ccd.debit-ccd.credit
			credit=0.0
		elif ccd.debit<ccd.credit:
			debit=0.0
			credit=ccd.credit-ccd.debit
		else:
			debit=0.0
			credit=0.0
		
		opening_credit = 0
		opening_debit = 0
		for b in balances:
			if b.budget_against == ccd.budget_against:
				opening_credit = b.credit
				opening_debit = b.debit
		
		if opening_debit>opening_credit:
			opening_debit=opening_debit-opening_credit
			opening_credit=0
			dor=1
		elif opening_debit<opening_credit:
			opening_debit=0
			opening_credit=opening_credit-opening_debit						
			dor=0
		else:
			opening_debit=0
			opening_credit=0
			dor=2
		if dor==1:
			closing=(debit+credit)+(opening_debit)
		else:
			closing=(debit+credit)-(opening_debit)
		if closing>0:
			debit=closing
			credit=0.0
		elif closing<0:
			debit=0.0
			credit=closing
		else:
			debit=0.0
			credit=0.0

		if filters.get("budget_against")=="Task":
			data.append([ccd.budget_against, ccd.budget_against_name, ccd.project, opening_debit, opening_credit, ccd.debit, ccd.credit, debit, credit])			
		else:
			data.append([ccd.budget_against, ccd.budget_against_name, opening_debit, opening_credit, ccd.debit, ccd.credit, debit, credit])

	
	return columns, data

def get_columns(filters):
	columns = [
		_(filters.get("budget_against")) + ":Link/%s:120" % (filters.get("budget_against"))		
	]
	if filters.budget_against == "Task":
		columns.append(_("Subject") + ":Data:200")
		columns.append(_("Project") + ":Link/Project:100")		
	else:
		columns.append(_(filters.get("budget_against")+" Name") + ":Data:200")
	columns.append("Opening (Dr)):Currency:120")
	columns.append("Opening (Cr):Currency:120")
	columns.append("Debit:Currency:120")
	columns.append("Credit:Currency:120")
	columns.append("Closing (Dr):Currency:120")
	columns.append("Closing (Cr):Currency:120")
	return columns

def get_cost_centers(filters):
	order_by = ""
	if filters.get("budget_against") == "Cost Center":
		order_by = "order by lft"

	if filters.get("budget_against") in ["Cost Center", "Project"]:
		return frappe.db.sql_list(
			"""
				select
					name
				from
					`tab{tab}`
				where
					company = %s
				{order_by}
			""".format(tab=filters.get("budget_against"), order_by=order_by),
			filters.get("company"))
	else:
		return frappe.db.sql_list(
			"""
				select
					name
				from
					`tab{tab}`
			""".format(tab=filters.get("budget_against")))  # nosec

def get_dimension_target_details(dimensions,filters):
	budget_against = frappe.scrub(filters.get("budget_against"))
	cond = ""
	col = """ bal.{budget_against}_name """
	if filters.budget_against == "Task" and filters.get('project'):
	 	cond += """and bal.project = %s""" % (frappe.db.escape(filters.get('project')))

	if filters.budget_against == "Task":
		col= """ bal.project as project, bal.subject """
	else:
		col= """ bal.{budget_against}_name """
		col = """ bal.%s_name """ % (budget_against)
	if filters.get('account'):
		cond += """and acc.name = %s""" % (frappe.db.escape(filters.get('account')))

	if dimensions:
		cond += """ and b.{budget_against} in (%s)""".format(
			budget_against=budget_against) % ", ".join(["%s"] * len(dimensions))
		if filters.root_type:
			cond+= " and acc.root_type in (%s)" % ( ", ".join(["%s"] * len(filters.root_type)))
			dimensions += filters.root_type

	return frappe.db.sql(
		"""
			select
				b.{budget_against} as budget_against,
				{col} as budget_against_name,
				sum(b.debit) as debit,
				sum(b.credit) as credit
			from
				`tabGL Entry` b	 
			INNER JOIN `tab{budget_against_label}` bal on b.{budget_against}=bal.name
			INNER JOIN `tabAccount` acc on b.account=acc.name 
			where				
				b.company = %s
				and b.posting_date between %s and %s 
				{cond}
			group by
				b.{budget_against}
		""".format(
			budget_against_label=filters.budget_against,
			budget_against=budget_against,
			cond=cond,
			col=col
		),
		tuple(
			[
				filters.company,
				filters.from_date,
				filters.to_date,
			]
			+ dimensions
		), as_dict=True)

def get_opening_balances(dimensions,filters):
	budget_against = frappe.scrub(filters.get("budget_against"))
	cond = ""
	if filters.budget_against == "Task" and filters.get('project'):
	 	cond += """and bal.project = %s""" % (frappe.db.escape(filters.get('project')))

	if filters.get('account'):
		cond += """and acc.name = %s""" % (frappe.db.escape(filters.get('account')))

	if dimensions:
		cond += """ and b.{budget_against} in (%s)""".format(
			budget_against=budget_against) % ", ".join(["%s"] * len(dimensions))
		if filters.root_type:
			cond+= " and acc.root_type in (%s)" % ( ", ".join(["%s"] * len(filters.root_type)))
			dimensions += filters.root_type

	return frappe.db.sql(
		"""
			select
				b.{budget_against} as budget_against,				
				sum(b.debit) as debit,
				sum(b.credit) as credit
			from
				`tabGL Entry` b	 
			INNER JOIN `tab{budget_against_label}` bal on b.{budget_against}=bal.name
			INNER JOIN `tabAccount` acc on b.account=acc.name 
			where				
				b.company = %s
				and b.posting_date < %s 
				{cond}
			group by
				b.{budget_against}
		""".format(
			budget_against_label=filters.budget_against,
			budget_against=budget_against,
			cond=cond,
		),
		tuple(
			[
				filters.company,
				filters.from_date,
			]
			+ dimensions
		), as_dict=True)
