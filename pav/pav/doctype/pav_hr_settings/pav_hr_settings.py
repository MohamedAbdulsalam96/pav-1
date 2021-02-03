# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from frappe.utils import getdate, add_days, today
from frappe.model.document import Document

class PAVHRSettings(Document):
	def validate(self):
		'''leave_auto_approve'''
		enable_auto_approve_leave = frappe.db.get_single_value("PAV HR Settings", "enable_auto_approve_leave")
		if enable_auto_approve_leave==1 :
			from_workflow_state=frappe.db.get_single_value('PAV HR Settings', 'from_workflow_state')
			to_workflow_state=frappe.db.get_single_value('PAV HR Settings', 'to_workflow_state')
			period=frappe.db.get_single_value('PAV HR Settings', 'period')
			leaves = frappe.get_all("Leave Application",
				fields=["name"],
				filters={'workflow_state' : from_workflow_state, 'posting_date':('<=',add_days(today(),(period-(period*2))))})
			for leave in leaves:
				frappe
				leave_obj = frappe.get_doc("Leave Application",leave.name)
				leave_obj.workflow_state = to_workflow_state
				leave_obj.add_comment('Comment', text='Auto ({0}), More Than {1} Lating From Leave Approver'.format(to_workflow_state,period))				
				leave_obj.save()				
				##leave_obj.db_set("workflow_state", to_workflow_state, update_modified=False)