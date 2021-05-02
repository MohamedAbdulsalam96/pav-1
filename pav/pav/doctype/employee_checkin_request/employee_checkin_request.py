# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_datetime,formatdate,format_time
from frappe.model.document import Document

class EmployeeCheckinRequest(Document):
	def validate(self):
		if not self.employee or not self.log_type:
			frappe.throw(_("""Employee and Log Type are mandatory"""))

	
	def on_submit(self):
		if self.approval_status=="Open":
			frappe.throw(_("""Approval Status must be 'Approved' or 'Rejected'"""))
		elif self.approval_status=='Approved': 
			self.create_checkin()

	def create_checkin(self):
		emp = frappe.get_doc("Employee", self.employee)
		if not emp.default_shift:
			frappe.throw(_("""Employee should to have Default Shift"""))
		shift = frappe.get_doc("Shift Type", emp.default_shift)
		if self.enable_two_period_in_ecr==1:
			if self.period_type=='First':
				if self.log_type=='ALL':
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": "IN",
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.start_time)),
						"employee_checkin_request": self.name
					}))
					ec.insert()
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": "OUT",
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.end_first_period)),
						"employee_checkin_request": self.name
					}))
					ec.insert()
				else:
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": self.log_type,
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.start_time if self.log_type=='IN' else shift.end_first_period)),
						"employee_checkin_request": self.name
					}))
					ec.insert()
			elif self.period_type=='Second':
				if self.log_type=='ALL':
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": "IN",
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.start_second_period)),
						"employee_checkin_request": self.name
					}))
					ec.insert()
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": "OUT",
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.end_time)),
						"employee_checkin_request": self.name
					}))
					ec.insert()
				else:
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": self.log_type,
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.start_second_period if self.log_type=='IN' else shift.end_time)),
						"employee_checkin_request": self.name
					}))
					ec.insert()
			elif self.period_type=='ALL':
				if self.log_type=='ALL':
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": "IN",
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.start_time)),
						"employee_checkin_request": self.name
					}))
					ec.insert()
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": "OUT",
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.end_first_period)),
						"employee_checkin_request": self.name
					}))
					ec.insert()
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": "IN",
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.start_second_period)),
						"employee_checkin_request": self.name
					}))
					ec.insert()
					ec = frappe.get_doc(frappe._dict({
						"doctype": "Employee Checkin",
						"employee": self.employee,
						"log_type": "OUT",
						"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.end_time)),
						"employee_checkin_request": self.name
					}))
					ec.insert()	
				else:
					frappe.throw(_("""If the Period Type equal ALL, the Log Type should to be ALL"""))
		else:
			if self.log_type=='ALL':
				ec = frappe.get_doc(frappe._dict({
					"doctype": "Employee Checkin",
					"employee": self.employee,
					"log_type": "IN",
					"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.start_time)),
					"employee_checkin_request": self.name
				}))
				ec.insert()
				ec = frappe.get_doc(frappe._dict({
					"doctype": "Employee Checkin",
					"employee": self.employee,
					"log_type": "OUT",
					"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.end_time)),
					"employee_checkin_request": self.name
				}))
				ec.insert()
			else:
				ec = frappe.get_doc(frappe._dict({
					"doctype": "Employee Checkin",
					"employee": self.employee,
					"log_type": self.log_type,
					"time": get_datetime(formatdate(self.date,'YYYY-mm-dd')+' '+format_time(shift.start_time if self.log_type=='IN' else shift.end_time)),
					"employee_checkin_request": self.name
				}))
				ec.insert()