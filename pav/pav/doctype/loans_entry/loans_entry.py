# -*- coding: utf-8 -*-
# Copyright (c) 2021, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from dateutil.relativedelta import relativedelta
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff
from frappe import _
from erpnext.accounts.utils import get_fiscal_year
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee

class LoansEntry(Document):
	def on_submit(self):
		self.status="Sanctioned"		
		self.create_loans()

	def validate(self):
		if self.get('employees'):
			for emp in self.get('employees'):
				if emp.total_amount<=0:
					frappe.throw(_("The Amount of Employee {0} must be greater than Zero").format(emp.employee))
				count2=0
				for emp2 in self.get('employees'):
					if emp.employee==emp2.employee:
						count2=count2+1
						if count2>1:
							frappe.throw(_("Employee {0} must be one in table").format(emp.employee))
		
	def get_emp_list(self):
		emp_list = frappe.db.sql("""
				select
					distinct t1.name as employee, t1.employee_name, t1.department, t1.designation ,t1.adding_loan ,t1.loan_type,t1.amount as total_amount
				from
					`tabEmployee` t1, `tabSalary Structure Assignment` t2 where t1.name = t2.employee and t1.status='Active'""", as_dict=True)
		return emp_list

	def get_employees_loans(self):	
		self.set('employees', [])
		employees = self.get_emp_list()
		if not employees:
			frappe.throw(_("No employees for the mentioned criteria"))
		else:
			for d in employees:
				#d.total_amount= d.base_salary * (d.rate_of_loans/100)
				if  d.adding_loan and (d.loan_type==self.loan_type) :
					self.append('employees', d)
					self.number_of_employees = len(employees)
	
	def get_all_employees(self):
	
		self.set('employees', [])
		employees = self.get_emp_list()
		if not employees:
			frappe.throw(_("No employees for the mentioned criteria"))
		else:
			for d in employees:
				#d.total_amount= d.base_salary * (d.rate_of_loans/100)
				if self.amount and  self.loan_type :
					d.total_amount=self.amount
					self.append('employees', d)
					self.number_of_employees = len(employees)

	def clear_table(self):
		self.set('employees', [])	

	def get_filter_condition(self):
		self.check_mandatory()

		cond = ''
		for f in ['company', 'branch', 'department', 'designation']:
			if self.get(f):
				cond += " and t1." + f + " = '" + self.get(f).replace("'", "\'") + "'"

		return cond

	def check_mandatory(self):
		for fieldname in ['company']:
			if not self.get(fieldname):
				frappe.throw(_("Please set {0}").format(self.meta.get_label(fieldname)))
	
	def create_loans(self):
		if self.employees:			
			for m in self.get("employees"):
				log_args=frappe._dict({
					"doctype":"Loan",
					#"gird_loans_employee": self.name,
					"applicant":m.employee,
					"loan_type": self.loan_type,
					"loans_entry": self.name,
					"loan_amount" :m.total_amount,
					"status":self.status,
					"repay_from_salary":self.repay_from_salary,
					"repayment_start_date":self.repayment_start_date,
					"repayment_method": self.repayment_method,
					"repayment_periods":self.repayment_periods,
					"mode_of_payment" : self.mode_of_payment,
					"payment_account" : self.payment_account,
					"loan_account" : self.loan_account,
					"interest_income_account" : self.interest_income_account,
				})
				il = frappe.get_doc(log_args)
				il.insert()
	