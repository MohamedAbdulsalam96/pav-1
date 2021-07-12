# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import (flt,cstr)
from datetime import datetime,timedelta,time

def delay(max, min):
	return max - min if max and min and max > min else timedelta(00,00,00)

def delayTotal(max, min):
	if max and min:
		return max + min
	elif max and not min:
		return max
	elif min and not max:
		return min 
	else:
		timedelta(00,00,00)

def execute(filters=None):
	if not filters: filters = {}
	formatted_data = []
	columns = get_columns()
	data = get_data(filters)

	t= timedelta(00,00,00)
	#dd= timedelta(hours=t.hours,minutes=t.minutes)\
	empList = []
	for d in data:
			startLate = delay(d[3], d[5])
			endLate = delay(d[6], d[4])
			tLate = delayTotal(startLate, endLate)

			startEr = delay(d[5], d[3])
			endEr = delay(d[4], d[6])
			tEr = delayTotal(startEr, endEr)
			tHours=d[4] - d[3] if d[4] and d[3] and d[4] > d[3] else timedelta(00,00,00)
			if empList:
				chk = False
				for e in empList:
					if e[0] == d[0]:
						chk = True
						
						e[5] = delayTotal(e[5], startLate)
						e[6] =  delayTotal(e[6], endLate)
						e[7] =  delayTotal(e[7], tLate)
						e[8] =  delayTotal(e[8], startEr)
						e[9] =  delayTotal(e[9], endEr)
						e[10] = delayTotal(e[10], tEr)
						e[11] = delayTotal(e[11], tHours)
				if not chk:
					empList.append([d[0], d[1], d[2], d[3], d[4], startLate, endLate, tLate, startEr, endEr, tEr, tHours])
			else:
				empList.append([d[0], d[1], d[2], d[3], d[4], startLate, endLate, tLate, startEr, endEr, tEr, tHours])

	for d in empList:
			formatted_data.append({
			"emponly": d[0],
			"empname": d[1],
			"dateonly": d[2],
			"mintime": d[3],
			"maxtime": d[4],
			"late_entry":  d[5],
			"early_exit": d[6],
			"delay_total" : to_hours(d[7]) , 
			"early_entry" : d[8],
			"late_exit" : d[9], 
			"early_total" : to_hours(d[10]),
			"workinghours": to_hours(d[11]),	})
				
	formatted_data.extend([{}])
	return columns, formatted_data

def to_hours(duration):
	if duration:
		totsec = duration.total_seconds()
		h = totsec//3600
		m = (totsec%3600) // 60
		sec =(totsec%3600)%60
		return "%d:%d:%d" %(h,m,sec)
	else:
		return timedelta(00,00,00)

def get_columns():
	return [
		{
			"fieldname": "emponly",
			"label": _("Employee "),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120
		},
		{
			"fieldname": "empname",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 170
		},
		
		
                {
			"fieldname": "late_entry",
			"label": _("Late Entry"),
			"fieldtype": "Data",
			"width": 80
		},
			        {
			"fieldname": "early_exit",
			"label": _("Early Exit"),
			"fieldtype": "Data",
			"width": 80
		},
		      {
			"fieldname": "delay_total",
			"label": _("Delay Total"),
			"fieldtype": "Data",
			"width": 85
		},
		 {
			"fieldname": "early_entry",
			"label": _("Early Entry"),
			"fieldtype": "Data",
			"width": 80
		 },
		 		{
			"fieldname": "late_exit",
			"label": _("Late Exit"),
			"fieldtype": "Data",
			"width": 80
		},
		{
			"fieldname": "early_total",
			"label": _("Early Total"),
			"fieldtype": "Data",
			"width": 85
		},
		 {
			"fieldname": "workinghours",
			"label": _("Working Hours"),
			"fieldtype": "Data",
			"width": 120
		},
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

		(select TIME(MIN(l.shift_start)) FROM `tabEmployee Checkin` l where l.employee=em.employee and 
			DATE(l.time)<= DATE(em.time) and DATE(l.time)>= DATE(em.time) limit 1) as shift_start,
		(select TIME(MAX(l.shift_end)) FROM `tabEmployee Checkin` l where l.employee=em.employee and 
			DATE(l.time)<= DATE(em.time) and DATE(l.time)>= DATE(em.time) limit 1) as shift_end

		FROM `tabEmployee Checkin` em
		{conditions} GROUP BY dateonly, employee
		""".format(
			conditions=get_conditions(filters),
		),
		filters, as_list=1)
	##frappe.msgprint("ini_list={0}".format(ini_list))

	return ini_list

