# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from dateutil.relativedelta import relativedelta
from frappe.utils import cint, flt
from frappe import _

class PayrollEntryTool(Document):
	def on_submit(self):
		self.make_accrual_jv_entry()

	def get_default_payroll_payable_account(self):
		payroll_payable_account = self.payroll_account
		if not payroll_payable_account:
			frappe.throw(_("Please set Payroll Payable Account in Company Current Document")
				.format(self.company))
		return payroll_payable_account

	def get_loan_details(self,employee=None):
		"""
			Get loan details from submitted salary slip based on selected criteria
		"""
		cond = self.get_filter_condition(employee=employee)
		return frappe.db.sql(""" select eld.loan_account, eld.loan,
				eld.interest_income_account, eld.principal_amount, eld.interest_amount, eld.total_payment,t1.employee
			from
				`tabSalary Slip` t1, `tabSalary Slip Loan` eld
			where
				t1.docstatus = 1 and t1.name = eld.parent and start_date >= %s and end_date <= %s %s
			""" % ('%s', '%s', cond), (self.start_date, self.end_date), as_dict=True) or []


	def get_salary_component_account(self, salary_component):
		account = frappe.db.get_value("Salary Component Account",
			{"parent": salary_component, "company": self.company}, "default_account")

		if not account:
			frappe.throw(_("Please set default account in Salary Component {0}")
				.format(salary_component))

		return account

	def get_filter_condition(self,employee=None):
		##self.check_mandatory()

		cond = ''
		for f in ['company', 'payroll_entry']:
			if self.get(f):
				cond += " and t1." + f + " = '" + self.get(f).replace("'", "\'") + "'"
				if employee:
					cond += " and t1.employee = '" + employee + "'"

		return cond

	def get_sal_slip_list(self, ss_status, as_dict=False, employee=None):
		"""
			Returns list of salary slips based on selected criteria
		"""
		cond = self.get_filter_condition(employee=employee)

		ss_list = frappe.db.sql("""
			select t1.name, t1.employee, t1.net_pay from `tabSalary Slip` t1
			where t1.docstatus = %s and t1.start_date >= %s and t1.end_date <= %s
			and (t1.journal_entry is null or t1.journal_entry = "") %s
		""" % ('%s', '%s', '%s', cond), (ss_status, self.start_date, self.end_date), as_dict=as_dict)
		return ss_list

	def get_salary_components(self, component_type, employee=None):
		salary_slips = self.get_sal_slip_list(ss_status = 1, as_dict = True, employee=employee)
		if salary_slips:
			salary_components = frappe.db.sql("""select salary_component, amount, parentfield
				from `tabSalary Detail` where parentfield = '%s' and parent in (%s)""" %
				(component_type, ', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=True)
			return salary_components

	def get_salary_component_total(self, component_type = None, employee=None):
		salary_components = self.get_salary_components(component_type, employee=employee)
		if salary_components:
			component_dict = {}
			for item in salary_components:
				add_component_to_accrual_jv_entry = True
				if component_type == "earnings":
					is_flexible_benefit, only_tax_impact = frappe.db.get_value("Salary Component", item['salary_component'], ['is_flexible_benefit', 'only_tax_impact'])
					if is_flexible_benefit == 1 and only_tax_impact ==1:
						add_component_to_accrual_jv_entry = False
				if add_component_to_accrual_jv_entry:
					component_dict[item['salary_component']] = component_dict.get(item['salary_component'], 0) + item['amount']
			account_details = self.get_account(component_dict = component_dict,component_type=component_type,employee=employee)
			return account_details

	def get_account(self, component_dict = None,component_type=None,employee=None):
		account_dict = {}
		for s, a in component_dict.items():
			if component_type == "earnings":
				account = self.get_salary_component_account(s)
				if not account_dict.get(account):
					account_dict[s] = {}
					account_dict[s]['account']=account
					account_dict[s]['salary_component']=s

				account_dict[s]['amount'] = flt(account_dict[s].get('amount', 0.0) + a)
			else:
				account = self.get_salary_component_account(s)
				account_dict[account] = account_dict.get(account, 0) + a

		if account_dict and component_type == "earnings":
			account_dict2 = {}
			num=0
			for ac in account_dict:
				pa = frappe.db.sql("""select DISTINCT pa.name as project_activities, pa.project_dimension as project_dimension, pa.project as project, IFNULL(pap.project_percentage,0.0) as project_percentage
					from `tabProject Activities` pa 
					LEFT JOIN `tabSalary Component` sc ON sc.name = '%(sc)s'
					INNER JOIN `tabProject Activity Payroll` pap ON pap.parent = pa.name
					LEFT JOIN `tabProject Activity Salary Component` pasc ON pasc.parent = pa.name
					where (pasc.salary_component = '%(sc)s' or sc.depends_on_pa_sc = 1)
					and pap.employee = '%(employee)s' and pap.status= 'Active'""" %
					{"sc": ac,"employee":employee}, as_dict=True)

				if pa:
					percentage_count=0.0
					for item in pa:
						percentage_count+=item.project_percentage
						account_dict2[num]={}
						account_dict2[num]['account']=account_dict[ac].get('account')
						account_dict2[num]['amount']=flt(account_dict[ac].get('amount'))*flt(item.project_percentage)/100
						account_dict2[num]['project_activities']=item.project_activities
						account_dict2[num]['project']=item.project
						account_dict2[num]['project_dimension']=item.project_dimension
						account_dict2[num]['cost_center']=self.cost_center
						num+=1
					if percentage_count<100:
						percentage_count=100-percentage_count
						account_dict2[num]={}
						account_dict2[num]['account']=account_dict[ac].get('account')
						account_dict2[num]['amount']=account_dict[ac].get('amount')*percentage_count/100
						account_dict2[num]['project_activities']=self.project_activities
						account_dict2[num]['project']=self.project
						account_dict2[num]['project_dimension']=self.project_dimension
						account_dict2[num]['cost_center']=self.cost_center
						num+=1
					elif percentage_count>100:
						frappe.throw(_("Total Percentage of {0} is {1}")
						.format(employee,percentage_count))

				else:
					account_dict2[num]={}
					account_dict2[num]['account']=account_dict[ac].get('account')
					account_dict2[num]['amount']=account_dict[ac].get('amount')
					account_dict2[num]['project_activities']=self.project_activities
					account_dict2[num]['project']=self.project
					account_dict2[num]['project_dimension']=self.project_dimension
					account_dict2[num]['cost_center']=self.cost_center
					num+=1
			return account_dict2
		return account_dict

	def make_accrual_jv_entry(self):
		self.check_permission('write')
		deductions = self.get_salary_component_total(component_type = "deductions") or {}
		default_payroll_payable_account = self.get_default_payroll_payable_account()
		jv_name = ""
		precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")

		ss_list = self.get_sal_slip_list(ss_status=1)
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.voucher_type = 'Journal Entry'
		journal_entry.user_remark = _('Accrual Journal Entry for salaries from {0} to {1}')\
			.format(self.start_date, self.end_date)
		journal_entry.company = self.company
		journal_entry.posting_date = self.posting_date
		accounts = []
		earn=0.0
		ded=0.0
		loa=0.0
		pay=0.0

		for ss in ss_list:
			earnings = self.get_salary_component_total(component_type = "earnings",employee=ss[1]) or {}
			# Earnings
			for ear in sorted(earnings):
				accounts.append({
						"account": earnings[ear].get('account'),
						"debit_in_account_currency": flt(earnings[ear].get('amount'), precision),
						"cost_center": earnings[ear].get('cost_center'),
						"project": earnings[ear].get('project'),
						"project_dimension": earnings[ear].get('project_dimension'),
						"project_activities": earnings[ear].get('project_activities')
					})
				earn+=flt(earnings[ear].get('amount'), precision)
			# Loan
			loan_details = self.get_loan_details(employee=ss[1])
			for data in loan_details:
				accounts.append({
						"account": data.loan_account,
						"credit_in_account_currency": data.principal_amount,
						"party_type": "Employee",
						"party": data.employee
					})
				loa+=flt(data.principal_amount, precision)

				if data.interest_amount and not data.interest_income_account:
					frappe.throw(_("Select interest income account in loan {0}").format(data.loan))

				if data.interest_income_account and data.interest_amount:
					accounts.append({
						"account": data.interest_income_account,
						"credit_in_account_currency": data.interest_amount,
						"party_type": "Employee",
						"party": data.employee
					})
			# Payable amount
			accounts.append({
					"account": default_payroll_payable_account,
					"credit_in_account_currency": ss[2],
					"party_type": "Employee",
					"party": ss[1],
					"cost_center": earnings[ear].get('cost_center')
				})
			pay+=flt(ss[2], precision)


		# Deductions
		if deductions:
			# Deductions
			for acc, amount in deductions.items():
				accounts.append({
						"account": acc,
						"credit_in_account_currency": flt(amount, precision),
						"cost_center": self.cost_center,
						"party_type": '',
						"project": self.project
					})
				ded+=flt(amount, precision)

		##frappe.msgprint(_("Totals= earn={0}, ded={1}, loa={2}, pay={3}")
		##	.format(earn,ded,loa,pay))
		if not accounts:
			frappe.msgprint(_("There is no Submitted Salary Slip or may be its Acrrualed")
				.format(earn,ded,loa,pay))

		journal_entry.set("accounts", accounts)
		journal_entry.title = default_payroll_payable_account
		journal_entry.save()
		try:
			journal_entry.submit()
			jv_name = journal_entry.name
			self.update_salary_slip_status(jv_name = jv_name)
		except Exception as e:
			frappe.msgprint(e)

		frappe.msgprint(_("Journal Entry submitted for Payroll Entry period from {0} to {1}")
			.format(self.start_date, self.end_date))
		self.journal_entry_submitted=1

	def update_salary_slip_status(self, jv_name = None):
		ss_list = self.get_sal_slip_list(ss_status=1)
		for ss in ss_list:
			ss_obj = frappe.get_doc("Salary Slip",ss[0])
			frappe.db.set_value("Salary Slip", ss_obj.name, "journal_entry", jv_name)

