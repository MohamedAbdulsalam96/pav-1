# Copyright (c) 2021, Farouk Muharram and contributors
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
	for emp in data:
		basic_total = None
		over_total = None
		startLate = None
		endLate = None
		tLate = None
		startEr = None
		endEr = None
		tEr = None
		for d in data[emp]:
			if d[7] == "NOT NULL":
				temp= delay(d[4], d[3])
				basic_total = delayTotal(basic_total, temp)
				
				temp= delay(d[3], d[5])
				startLate = delayTotal(startLate, temp)
				temp = delay(d[6], d[4])
				endLate = delayTotal(endLate, temp)

				temp = delay(d[5], d[3])
				startEr = delayTotal(startEr, temp)
				temp = delay(d[4], d[6])
				endEr = delayTotal(endEr, temp)					
			elif d[7] == "NULL":
				temp= delay(d[4], d[3])
				over_total = delayTotal(over_total, temp)

		tLate = delayTotal(startLate, endLate)
		tEr = delayTotal(startEr, endEr)
		tHours = delayTotal(basic_total, over_total)
		formatted_data.append({
		"name": emp,
		"employee": d[0],
		"basic_total": to_hours(basic_total) if basic_total else basic_total,
		"over_total": to_hours(over_total) if over_total else over_total,
		"late_entry":   to_hours(startLate) if startLate else startLate,
		"early_exit":  to_hours(endLate) if endLate else endLate,
		"late_total" :  to_hours(tLate) if tLate else tLate,
		"early_entry" :  to_hours(startEr) if startEr else startEr,
		"late_exit" : to_hours(endEr) if endEr else endEr,
		"early_total" :  to_hours(tEr) if tEr else tEr,
		"working_hours": to_hours(tHours) if tHours else tHours,
			})
				
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
			"fieldname": "name",
			"label": _("Employee "),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120
		},
		{
			"fieldname": "employee",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 170
		},
		{
			"label": _("Shift Total"),
			"fieldtype": "Data",
			"fieldname": "basic_total",
			"width": 75

		},
		{
			"label": _("OverTime Total"),
			"fieldtype": "Data",
			"fieldname": "over_total",
			"width": 75

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
			"fieldname": "late_total",
			"label": _("Late Total"),
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
			"fieldname": "working_hours",
			"label": _("Working Hours"),
			"fieldtype": "Data",
			"width": 120
		},
	]
	
def get_conditions(filters):
	condition = " where date(time)>= '%s' and date(time)<= '%s' " % (filters.get("from"), filters.get("to"))
	if filters.get("employee"):
		condition += " AND employee ='%s' " % (filters.get('employee'))
	return condition


def get_data(filters):
	list_ = frappe.db.sql('''SELECT employee, employee_name, date(time) as ckin_date, shift, TIME(min(time)) as in_time,
		TIME(max(time)) as out_time, TIME(MAX(shift_start)) as shift_start, TIME(MAX(shift_end)) as shift_end, 
		IF(ISNULL(shift), 'NULL', 'NOT NULL') as shift_nullable
		FROM `tabEmployee Checkin` {0} GROUP BY employee, date(time), shift_nullable'''.format(get_conditions(filters)), as_list=1)

	result = {}
	for d in list_:
		result.setdefault(d[0], [])
		result[d[0]].append([d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8]])

	return result

