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
		data.append([ccd.budget_against, ccd.budget_against_name, ccd.debit, ccd.credit, debit, credit])

	
	return columns, data

def get_columns(filters):
	columns = [
		_(filters.get("budget_against")) + ":Link/%s:150" % (filters.get("budget_against")),
		_(filters.get("budget_against")+" Name") + ":Link/%s:300" % (filters.get("budget_against"))
	]	
	columns.append("Debit:Currency:150")
	columns.append("Credit:Currency:150")
	columns.append("Balance Debit:Currency:150")
	columns.append("Balance Credit:Currency:150")
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
	if dimensions:
		cond += """ and b.{budget_against} in (%s)""".format(
			budget_against=budget_against) % ", ".join(["%s"] * len(dimensions))
		if filters.root_type:
			cond+= " and acc.root_type =  '{0}' ".format(filters.root_type)

	return frappe.db.sql(
		"""
			select
				b.{budget_against} as budget_against,
				bal.{budget_against}_name as budget_against_name,
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
		),
		tuple(
			[
				filters.company,
				filters.from_date,
				filters.to_date	
			]
			+ dimensions
		), as_dict=True)