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
		debit = ccd.debit
		credit = ccd.credit
		
		opening_credit = 0
		opening_debit = 0
		for b in balances:
			if b.budget_against == ccd.budget_against:
				opening_credit = b.credit
				opening_debit = b.debit
				opening_debit, opening_credit = toggle_debit_credit(opening_debit, opening_credit)
		
		closing_debit, closing_credit = toggle_debit_credit(opening_debit + debit, opening_credit + credit)

		if filters.get("budget_against") in ["Task","Project Activities"] or filters.budget_against == "Property":
			data.append([ccd.budget_against, ccd.budget_against_name, ccd.project, opening_debit, opening_credit, debit, credit, closing_debit, closing_credit])			
		else:
			data.append([ccd.budget_against, ccd.budget_against_name, opening_debit, opening_credit, debit, credit, closing_debit, closing_credit])

	
	return columns, data

def toggle_debit_credit(debit, credit):
	if flt(debit) > flt(credit):
		debit = flt(debit) - flt(credit)
		credit = 0.0
	else:
		credit = flt(credit) - flt(debit)
		debit = 0.0

	return debit, credit

def get_columns(filters):
	columns = [
		_(filters.get("budget_against")) + ":Link/%s:120" % (filters.get("budget_against"))		
	]
	if filters.budget_against in ["Task","Project Activities"]:
		columns.append(_("Subject") + ":Data:300")
		columns.append(_("Project") + ":Link/Project:100")	
	else:
		columns.append(_(filters.get("budget_against")+" Name") + ":Data:300")
	columns.append("Opening (Dr):Currency:120")
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
	if ((filters.budget_against in ["Task","Project Activities"] or filters.budget_against == "Property" ) and filters.get('project')):
		cond += """and bal.project = %s""" % (frappe.db.escape(filters.get('project')))

	if filters.budget_against == "Task":
		col= """ bal.project as project, bal.subject """
	elif filters.budget_against == "Project Activities":
		col= """ bal.project as project, bal.project_activity """
	else:
		col= """ bal.{budget_against}_name """
		col = """ bal.%s_name """ % (budget_against)

	if dimensions:
		cond += """ and b.{budget_against} in (%s)""".format(
			budget_against=budget_against) % ", ".join(["%s"] * len(dimensions))
	
	if filters.root_type:
		if filters.get("account"):
			lft, rgt = frappe.db.get_value("Account", filters["account"], ["lft", "rgt"])
			cond += """and account in (select name from tabAccount
			where lft>=%s and rgt<=%s and docstatus<2)""" % (lft, rgt)
		else:
			cond+= " and acc.root_type in (%s)" % ( ", ".join(["%s"] * len(filters.root_type)))
			if not dimensions:
				dimensions = filters.root_type
			else:
				dimensions += filters.root_type
	else:
		if filters.get("account"):
			lft, rgt = frappe.db.get_value("Account", filters["account"], ["lft", "rgt"])
			cond += """and account in (select name from tabAccount
			where lft>=%s and rgt<=%s and docstatus<2)""" % (lft, rgt)

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
	col = """ bal.{budget_against}_name """

	if ((filters.budget_against in ["Task","Project Activities"] or filters.budget_against == "Property" ) and filters.get('project')):
		cond += """and bal.project = %s""" % (frappe.db.escape(filters.get('project')))

	if filters.budget_against == "Task":
		col= """ bal.project as project, bal.subject """
	elif filters.budget_against == "Project Activities":
		col= """ bal.project as project, bal.project_activity """
	else:
		col= """ bal.{budget_against}_name """
		col = """ bal.%s_name """ % (budget_against)

	if dimensions:
		cond += """ and b.{budget_against} in (%s)""".format(
			budget_against=budget_against) % ", ".join(["%s"] * len(dimensions))
	
	if filters.root_type:
		if filters.get("account"):
			lft, rgt = frappe.db.get_value("Account", filters["account"], ["lft", "rgt"])
			cond += """and account in (select name from tabAccount
			where lft>=%s and rgt<=%s and docstatus<2)""" % (lft, rgt)
		else:
			cond+= " and acc.root_type in (%s)" % ( ", ".join(["%s"] * len(filters.root_type)))
			if not dimensions:
				dimensions = filters.root_type
			else:
				dimensions += filters.root_type
	else:
		if filters.get("account"):
			lft, rgt = frappe.db.get_value("Account", filters["account"], ["lft", "rgt"])
			cond += """and account in (select name from tabAccount
			where lft>=%s and rgt<=%s and docstatus<2)""" % (lft, rgt)

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
				and b.posting_date < %s 
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
			]
			+ dimensions
		), as_dict=True)
