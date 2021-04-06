# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import (flt,cstr)

def execute(filters=None):
	if not filters: filters = {}
	formatted_data = []
	columns = get_columns()
	data = get_data(filters)
	for d in data:
		formatted_data.append({
			"emponly": d[0],
			"empname": d[1],
			"dateonly": d[2],
			"mintime": d[3],
			"maxtime": d[4],
			"delaytime": d[5] if d[8]<d[3] else None,
			"earlyentry":d[6] if d[8]>d[3] else None,
			"workinghours": d[7]
		})
	formatted_data.extend([{}])
	return columns, formatted_data

def get_columns():
	return [
		{
			"fieldname": "emponly",
			"label": _("Employee "),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150
		},
		{
			"fieldname": "empname",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "dateonly",
			"label": _("Date"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "mintime",
			"label": _("First"),
			"fieldtype": "Data",
			"width": 70
		},
		{
			"fieldname": "maxtime",
			"label": _("Last"),
			"fieldtype": "Data",
			"width": 70
		},
                {
			"fieldname": "delaytime",
			"label": _("Delay -"),
			"fieldtype": "Data",
			"width": 70
		},
		 {
			"fieldname": "earlyentry",
			"label": _("Early +"),
			"fieldtype": "Data",
			"width": 70
		 },
                {
			"fieldname": "workinghours",
			"label": _("Working hours"),
			"fieldtype": "Data",
			"width": 120
		}
		]


def get_conditions(filters):
	
	conditions = []
	if filters.get("employee"): conditions.append("em.employee = %(employee)s")
	if filters.get("from"): conditions.append("DATE(em.time) >= %(from)s")
	if filters.get("to"): conditions.append("DATE(em.time) <= %(to)s")	
	return "where {}".format(" and ".join(conditions)) if conditions else ""


def get_data(filters):
	ini_list = frappe.db.sql("""SELECT em.employee as 'emponly',
		em.employee_name as 'empname', DATE(em.time) as dateonly,
		(select TIME(MIN(l.time)) FROM `tabEmployee Checkin` l where l.employee=em.employee and 
			DATE(l.time)<= DATE(em.time) and DATE(l.time)>= DATE(em.time) limit 1) as mintime,
		(select TIME(MAX(l.time)) FROM `tabEmployee Checkin` l where l.employee=em.employee and 
			DATE(l.time)<= DATE(em.time) and DATE(l.time)>= DATE(em.time) limit 1) as maxtime,
		(select TIMEDIFF(time,shift_start)  FROM `tabEmployee Checkin` l where l.employee=em.employee and 
			DATE(l.time)<= DATE(em.time) and DATE(l.time)>= DATE(em.time) limit 1) as delaytime,
		(select TIMEDIFF(shift_start,time)  FROM `tabEmployee Checkin` l where l.employee=em.employee and 
			DATE(l.time)<= DATE(em.time) and DATE(l.time)>= DATE(em.time) limit 1) as earlyentry,
		(select TIMEDIFF(maxtime,mintime) FROM `tabEmployee Checkin` l where l.employee=em.employee and 
			DATE(l.time)<= DATE(em.time) and DATE(l.time)>= DATE(em.time) limit 1) as workinghour,
		(select TIME(MIN(l.shift_start)) FROM `tabEmployee Checkin` l where l.employee=em.employee and 
			DATE(l.time)<= DATE(em.time) and DATE(l.time)>= DATE(em.time) limit 1) as shift_start
		FROM `tabEmployee Checkin` em
		{conditions} GROUP BY dateonly, employee
		""".format(
			conditions=get_conditions(filters),
		),
		filters, as_list=1)
	##frappe.msgprint("ini_list={0}".format(ini_list))

	return ini_list
