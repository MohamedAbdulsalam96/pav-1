# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
from erpnext.accounts.report.trial_balance.trial_balance import validate_filters
from erpnext.accounts.party import get_party_account_currency

def execute(filters=None):
	data=[]
	validate_filters(filters)
	party_filters={}
	parties = frappe.get_all('Party Type', fields = ["name", "party_name_field"],
		filters = party_filters, order_by="name")
	# parties=['Customer', 'Supplier','Shareholder','Employee','Employee Account']
	for party in parties:
		show_party_name =True
		party_name_field = party.party_name_field or 'name'
		
		cond=""
		dim=[]
		pn=frappe.scrub(party.name)
		# frappe.msgprint("{0}".format(pn))
		if filters.get(pn):
			filters[pn] = frappe.parse_json(filters.get(pn))
			cond= """ where name in (%s)""" % ( ", ".join(["%s"] * len(filters.get(pn))))
			dim=filters.get(pn)
			# frappe.msgprint("{0}".format(filters.get(pn)))
			party_filters = {"name": party.name} if filters.get("party") else {}
			party_parties = frappe.db.sql(
				"""
					select
						name,{party_name_field}
					from
						`tab{tab}` {cond}
				""".format(tab=party.name,party_name_field=party_name_field,cond=cond),tuple(dim), as_dict=True)
			# parties = frappe.get_all(party, fields = ["name",party_name_field],
			# 	filters=party_filters,order_by="name")
			filters.party_type=party.name

			data+=get_data(filters,show_party_name,party_name_field=party_name_field,parties=party_parties)

	

	columns = get_columns(filters, show_party_name)
	# data = get_data(filters, show_party_name)

	return columns, data

def get_data(filters, show_party_name,party_name_field = 'name',parties=None):
	company_currency = frappe.get_cached_value('Company',  filters.company,  "default_currency")
	opening_balances = get_opening_balances(filters)
	balances_within_period = get_balances_within_period(filters)

	data = []
	# total_debit, total_credit = 0, 0
	total_row = frappe._dict({
		"opening_debit": 0,
		"opening_credit": 0,
		"debit": 0,
		"credit": 0,
		"closing_debit": 0,
		"closing_credit": 0
	})
	for party in parties:
		row = { "party_type": filters.get('party_type'),"party": party.name }
		# if show_party_name:
		row["party_name"] = party.get(party_name_field)
		row["party_currency"] = get_party_account_currency(filters.get('party_type'), party.name, filters.get('company'))

		# opening
		if filters.group_by_account:
			opening_debit, opening_credit, account= opening_balances.get(party.name, [0, 0,''])
		else:
			opening_debit, opening_credit = opening_balances.get(party.name, [0, 0])
		row.update({
			"opening_debit": opening_debit,
			"opening_credit": opening_credit
		})

		# within period
		debit, credit = balances_within_period.get(party.name, [0, 0])
		row.update({
			"debit": debit,
			"credit": credit
		})

		# closing
		closing_debit, closing_credit = toggle_debit_credit(opening_debit + debit, opening_credit + credit)
		row.update({
			"closing_debit": closing_debit,
			"closing_credit": closing_credit
		})

		# totals
		for col in total_row:
			total_row[col] += row.get(col)

		row.update({
			"currency": get_party_account_currency(filters.get('party_type'), party.name, filters.get('company')),
			"party_type_link":filters.get('party_type')			
		})
		if filters.group_by_account:
			row.update({
				"account":account
			})

		has_value = False
		if (opening_debit or opening_credit or debit or credit or closing_debit or closing_credit):
			has_value  =True

		if cint(filters.show_zero_values) or has_value:
			data.append(row)

	# Add total row

	##total_row.update({
	##	"party": "'" + _("Totals") + "'",
	##	"currency": company_currency
	##})
	##data.append(total_row)

	return data

def get_opening_balances(filters):

	account_filter = ''
	if filters.get('account'):
		account_filter = "and account = %s" % (frappe.db.escape(filters.get('account')))
	group_by_account=""
	if filters.group_by_account:
		group_by_account=", account"
	gle = frappe.db.sql("""
		select party, sum(debit_in_account_currency) as opening_debit, sum(credit_in_account_currency) as opening_credit {group_by_account}
		from `tabGL Entry`
		where company=%(company)s
			and ifnull(party_type, '') = %(party_type)s and ifnull(party, '') != ''
			and (posting_date < %(from_date)s or ifnull(is_opening, 'No') = 'Yes')
			{account_filter}
		group by party {group_by_account}""".format(account_filter=account_filter,group_by_account=group_by_account), {
			"company": filters.company,
			"from_date": filters.from_date,
			"party_type": filters.party_type,
		}, as_dict=True)

	opening = frappe._dict()
	for d in gle:
		opening_debit, opening_credit = toggle_debit_credit(d.opening_debit, d.opening_credit)
		if filters.group_by_account:
			opening.setdefault(d.party, [opening_debit, opening_credit,d.account])
		else:
			opening.setdefault(d.party, [opening_debit, opening_credit])

	return opening

def get_balances_within_period(filters):

	account_filter = ''
	if filters.get('account'):
		account_filter = "and account = %s" % (frappe.db.escape(filters.get('account')))
	group_by_account=""
	if filters.group_by_account:
		group_by_account=", account"
	gle = frappe.db.sql("""
		select party, sum(debit_in_account_currency) as debit, sum(credit_in_account_currency) as credit {group_by_account}
		from `tabGL Entry`
		where company=%(company)s
			and ifnull(party_type, '') = %(party_type)s and ifnull(party, '') != ''
			and posting_date >= %(from_date)s and posting_date <= %(to_date)s
			and ifnull(is_opening, 'No') = 'No'
			{account_filter}
		group by party {group_by_account}""".format(account_filter=account_filter,group_by_account=group_by_account), {
			"company": filters.company,
			"from_date": filters.from_date,
			"to_date": filters.to_date,
			"party_type": filters.party_type
		}, as_dict=True)

	balances_within_period = frappe._dict()
	for d in gle:
		balances_within_period.setdefault(d.party, [d.debit, d.credit])

	return balances_within_period

def toggle_debit_credit(debit, credit):
	if flt(debit) > flt(credit):
		debit = flt(debit) - flt(credit)
		credit = 0.0
	else:
		credit = flt(credit) - flt(debit)
		debit = 0.0

	return debit, credit

def get_columns(filters, show_party_name):
	columns = [
		{
			"fieldname": "party_type",
			"label": _("Party Type"),
			"fieldtype": "Data",			
			"width": 120
		},
		{
			"fieldname": "party",
			"label": _("Party Code"),
			"fieldtype": "Data",
			# "options": "party_type_link",
			"width": 150
		},
		{
			"fieldname": "party_name",
			"label": _("Party Name"),
			"fieldtype": "Data",			
			"width": 180
		},
		{
			"fieldname": "party_currency",
			"label": _("Party Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 50
		},
		{
			"fieldname": "opening_debit",
			"label": _("Opening (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "opening_credit",
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "closing_debit",
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "closing_credit",
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1
		}
	]

	if filters.group_by_account:
		columns.insert(3, {
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 150
		})

	return columns

def is_party_name_visible(party_type):
	show_party_name = False

	if party_type in ['Customer', 'Supplier']:
		if party_type == "Customer":
			party_naming_by = frappe.db.get_single_value("Selling Settings", "cust_master_name")
		else:
			party_naming_by = frappe.db.get_single_value("Buying Settings", "supp_master_name")

		if party_naming_by == "Naming Series":
			show_party_name = True
	else:
		show_party_name = True

	return show_party_name