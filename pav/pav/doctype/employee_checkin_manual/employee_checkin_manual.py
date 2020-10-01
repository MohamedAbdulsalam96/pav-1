# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import get_datetime
from frappe.model.document import Document

class EmployeeCheckinManual(Document):
	def validate(self):
		if not self.time: self.time=get_datetime()
	
	def on_submit(self):
		if self.approval_status=="Open":
			frappe.throw(_("""Approval Status must be 'Approved' or 'Rejected'"""))
		if self.approval_status=='Approved': self.create_checkin()

	def create_checkin(self):
		ec = frappe.get_doc(frappe._dict({
			"doctype": "Employee Checkin",
			"employee": self.employee,
			"log_type": self.log_type,
			"time": self.date+' '+self.time,
			"employee_checkin_manual": self.name
		}))
		ec.insert()



