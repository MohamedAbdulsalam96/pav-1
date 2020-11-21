# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import cstr, flt

class AttendanceSalaryTool(Document):
	def on_submit(self):
		self.make_accrual_jv_entry()
	def on_cancel(self):
		ss_list = self.get_sal_slip_list()
		for ss in ss_list:
			ss_obj = frappe.get_doc("Attendance",ss[0])
			frappe.db.set_value("Attendance", ss_obj.name, "attendance_salary_tool", "")


	def fill_employee_details(self):
		self.set('employees', [])
		employees = self.get_emp_list()
		if not employees:
			frappe.throw(_("No employees for the mentioned criteria"))
		self.total_attendance_days=0
		for d in employees:
			self.total_attendance_days+=d.attendance_days
			d.amount=d.attendance_days*self.day_rate
			self.append('employees', d)

		self.number_of_employees = len(employees)
		self.total_amount=self.day_rate*self.total_attendance_days

	def get_emp_list(self):
		"""
			Returns list of active employees based on selected criteria
			and for which salary structure exists
		"""
		condition= ''
		emp_list=[]
		if self.is_for_all==0:
			if not self.selected_employees:
				frappe.throw(_("No employees for the mentioned criteria"))
			#emp_list = [cstr(d.employee) for d in self.selected_employees]
			emp_list = frappe.db.sql_list("""
				select
					employee from `tabAttendance Salary Tool Employee`
				where
					parent = '%(parent)s' 
			"""%{"parent": self.name})
			condition+= """ and t1.employee IN %(employees)s """
		if self.is_open_period==0:
			if not self.start_date or not self.end_date:
				frappe.throw(_("Satart Date and End Date are Mandatories"))
			condition= """ and attendance_date >= %(start_date)s and attendance_date <= %(end_date)s"""
		emp_list = frappe.db.sql("""
			select
				t1.employee as employee, count(*) as attendance_days
			from
				`tabAttendance` t1
			where
				t1.attendance_salary_tool is null
				and t1.docstatus = 1 and t1.status='Present'
				{condition} group by t1.employee order by t1.employee asc
		""".format(condition=condition),{"employees": tuple(emp_list),"start_date": self.start_date,"end_date": self.end_date}, as_dict=True)
		return emp_list
	def make_accrual_jv_entry(self):
		if not self.employees:
			frappe.throw(_("No employees for current document"))
		if not self.payroll_payable_account:
			frappe.throw(_("Payroll Payable Account is mandatory"))
		if not self.expense_account:
			frappe.throw(_("Expense Account is mandatory"))

		self.check_permission('write')
		jv_name = ""
		precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.voucher_type = 'Journal Entry'
		journal_entry.user_remark = _('Accrual Journal Entry for salaries')
		journal_entry.company = self.company
		journal_entry.posting_date = self.posting_date
		accounts = []
		for emp in self.employees:
			accounts.append({
				"account": self.payroll_payable_account,
				"debit_in_account_currency": flt(emp.amount, precision),
				"party_type": "Employee",
				"party": emp.employee,
				"cost_center": self.cost_center
			})
		accounts.append({
			"account": self.expense_account,
			"credit_in_account_currency": flt(self.total_amount, precision),
			"cost_center": self.cost_center
		})
		if not accounts:
			frappe.msgprint(_("There is no Submitted Salary Slip or may be its Acrrualed"))

		journal_entry.set("accounts", accounts)
		journal_entry.title = self.payroll_payable_account
		journal_entry.save()
		self.accrual_jv=journal_entry.name
		self.save()
		try:
			journal_entry.submit()
			jv_name = journal_entry.name
			self.update_salary_slip_status(jv_name = jv_name)

		except Exception as e:
			frappe.msgprint(e)

		frappe.msgprint(_("Journal Entry submitted for Payroll Entry period from {0} to {1}")
			.format(self.start_date, self.end_date))
	def update_salary_slip_status(self, jv_name = None):
		ss_list = self.get_sal_slip_list()
		for ss in ss_list:
			ss_obj = frappe.get_doc("Attendance",ss[0])
			frappe.db.set_value("Attendance", ss_obj.name, "attendance_salary_tool", self.name)

	def get_sal_slip_list(self, as_dict=False):
		"""
			Returns list of active employees based on selected criteria
			and for which salary structure exists
		"""
		condition= ''
		emp_list=[]
		if self.is_for_all==0:
			if not self.selected_employees:
				frappe.throw(_("No employees for the mentioned criteria"))
			#emp_list = [cstr(d.employee) for d in self.selected_employees]
			emp_list = frappe.db.sql_list("""
				select
					employee from `tabAttendance Salary Tool Employee`
				where
					parent = '%(parent)s' 
			"""%{"parent": self.name})
			condition+= """ and t1.employee IN %(employees)s """
		if self.is_open_period==0:
			if not self.start_date or not self.end_date:
				frappe.throw(_("Satart Date and End Date are Mandatories"))
			condition= """ and attendance_date >= %(start_date)s and attendance_date <= %(end_date)s"""
		emp_list = frappe.db.sql("""
			select
				t1.name
			from
				`tabAttendance` t1
			where
				t1.attendance_salary_tool is null
				and t1.docstatus = 1 and t1.status='Present'
				{condition} group by t1.employee order by t1.employee asc
		""".format(condition=condition),{"employees": tuple(emp_list),"start_date": self.start_date,"end_date": self.end_date}, as_dict=as_dict)

		return emp_list