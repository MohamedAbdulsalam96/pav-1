# Developed By Walid alkubati on 13-5-2021

# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import erpnext
import datetime
from frappe import utils
from frappe.utils.dateutils import get_from_date_from_timespan, get_dates_from_timegrain, get_period_ending, parse_date
from erpnext import get_company_currency, get_default_company
from erpnext.accounts.report.utils import get_currency, convert_to_presentation_currency
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict


def execute(filters=None):
    if getdate(filters.fromdate).year != getdate(filters.todate).year:
        frappe.throw(_("From Date and To Date should be in the same year"))
        return [], []

    if filters.fromdate > filters.todate:
        frappe.throw(_("To Date Can Not be Less Then From Date"))
        return [], []

    columns, data = [], []
    #columns=["Ckin Date","Day Name","In Time","Out Time","Working Hours","Attendance Status","Pending Leave App","Pending Attendace Request"]
    columns = [
        {
            "label": _("Ckeckin Date"),
            "fieldtype": "Date",
            "fieldname": "ckin_date"

        },
        {
            "label": _("Day Name"),
            "fieldtype": "Data",
            "fieldname": "day_name",
            "width": 150

        },
        {
            "label": _("In Time"),
            "fieldtype": "Time",
            "fieldname": "in_iime"

        },
        {
            "label": _("Out Time"),
            "fieldtype": "Time",
            "fieldname": "out_iime"

        },
        {
            "label": _("Working Hours"),
            "fieldtype": "Time",
            "fieldname": "working_hours"

        },
        {
            "label": _("Attendance Status"),
            "fieldtype": "Data",
            "fieldname": "attendance_status"

        },
        {
            "label": _("Leave Application"),
            "fieldtype": "Link",
            "fieldname": "pending_leave_app",
            "options": "Leave Application",
            "width": 150
        },
        {
            "label": _("Attendace Request"),
            "fieldtype": "Link",
            "fieldname": "pending_attendace_request",
            "options": "Attendance Request",
            "width": 150
        },

    ]
    start_date = filters.get("fromdate")
    end_date = filters.get("todate")
    for d in get_dates_from_timegrain(filters.get("fromdate"), filters.get("todate")):
        row = [d, frappe.utils.data.get_weekday(d), '', '', '', '', '', '']
        data.append(row)
        conditions = get_conditions(filters)
    sq = frappe.db.sql("""SELECT  date(time) as ckin_date,time(min(time)) as in_time,time(max(time)) as out_time,TIMEDIFF(time(max(time)),time(min(time))) as working_hours 
	FROM `tabEmployee Checkin` %s""" % conditions, as_dict=1)
    # frappe.throw("{0}".format(sq))
    for at in sq:
        for dd in data:
            if at.ckin_date == dd[0]:
                dd[2] = at.in_time
                dd[4] = at.working_hours
                if at.in_time != at.out_time:
                    dd[3] = at.out_time

    emp_hl_conditions = get_emp_hl_conditions(filters)
    ho_list = frappe.db.sql("""SELECT case when emp.holiday_list is null then shift.holiday_list else emp.holiday_list end as emp_holiday_list FROM tabEmployee emp left join `tabShift Type` shift on emp.default_shift=shift.name %s""" % emp_hl_conditions, as_dict=1)
    stremp_hl = ho_list[0].emp_holiday_list
    holidays_conditions = get_holidays_conditions(filters, stremp_hl)
#	holidays_conditions=get_holidays_conditions(filters)
    holidays_list = frappe.db.sql(
        """SELECT distinct(holiday_date)as holiday_date FROM tabHoliday  %s""" % holidays_conditions, as_dict=1)

    for hdate in holidays_list:
        for dd5 in data:
            if hdate.holiday_date == dd5[0]:
                dd5[5] = 'Holiday'

    att_conditions = get_att_conditions(filters)
    emp_attendance = frappe.db.sql(
        """SELECT attendance_date,status FROM tabAttendance %s""" % att_conditions, as_dict=1)
    for at2 in emp_attendance:
        for dd2 in data:
            if at2.attendance_date == dd2[0]:
                dd2[5] = at2.status

    str_date = ""
    for dd3 in data:
        if (dd3[5] == '' or dd3[5] == 'Half Day') and dd3[1] != 'Friday' and dd3[1] != 'Saturday':
            # leave_conditions=get_leave_conditions(filters,parse_date(dd3[0]))
            str_date = dd3[0].strftime("%Y-%m-%d")
            leave_conditions = get_leave_conditions(filters, str_date)
            emp_leave = frappe.db.sql(
                """SELECT name FROM `tabLeave Application` %s""" % leave_conditions, as_dict=1)
            emp_att_req = frappe.db.sql(
                """SELECT name FROM `tabAttendance Request` %s""" % leave_conditions, as_dict=1)
            for le in emp_leave:
                dd3[6] = le.name
            for ar in emp_att_req:
                dd3[7] = ar.name
    total_p = 0.0
    total_l = 0.0
    total_a = 0.0
    total_h = 0.0
    total_hd = 0.0
    total_unkown = 0.0
    for dt in data:
        if dt[5] == 'Present':
            total_p += 1
        elif dt[5] == 'Absent':
            total_a += 1
        elif dt[5] == 'On Leave':
            total_l += 1
        elif dt[5] == 'Half Day':
            total_hd += 1
        elif dt[5] == 'Holiday':
            total_h += 1
        elif dt[5] == '':
            total_unkown += 1

    row = [None, 'Total Present', '', '', '', total_p, '', '']
    data.append(row)

    row = [None, 'Total Absent', '', '', '', total_a, '', '']
    data.append(row)

    row = [None, 'Total Leaves', '', '', '', total_l, '', '']
    data.append(row)

    row = [None, 'Total Half Days', '', '', '', total_hd, '', '']
    data.append(row)

    row = [None, 'Total Holidays', '', '', '', total_h, '', '']
    data.append(row)

    row = [None, 'Total Not Submitted', '', '', '', total_unkown, '', '']
    data.append(row)

    return columns, data


def get_holidays_conditions(filters, P_hol_list=None):
    conditions = " where parent='" + P_hol_list + "'"
    conditions += " and holiday_date>='" + \
        filters.get("fromdate") + "' and holiday_date<='" + \
        filters.get("todate") + "'"
    return conditions

# def get_holidays_conditions(filters):
 #       conditions = " where holiday_date>='" + filters.get("fromdate") + "' and holiday_date<='" + filters.get("todate") + "'"
#	return conditions

def get_emp_hl_conditions(filters):
    conditions = " where emp.name ='" + filters.get("employee") + "'"
    return conditions

def get_leave_conditions(filters, theDate=None):
    conditions = " where employee ='" + filters.get("employee") + "'"
    conditions += " and from_date<='" + theDate + "' and to_date>='" + theDate + "'"
    return conditions

def get_att_conditions(filters):
    conditions = " where docstatus=1 and employee ='" + \
        filters.get("employee") + "'"
    conditions += " and attendance_date>='" + \
        filters.get("fromdate") + "' and attendance_date<='" + \
        filters.get("todate") + "'"
    return conditions

def get_conditions(filters):
    #start_date = filters.get("fromdate")
    #end_date = filters.get("todate")
    conditions = ""
    # conditions = " where time(time)>='06:00' and time(time)<='18:10' "
    if filters.get("employee"):
        conditions += " where employee ='" + filters.get("employee") + "'"
    conditions += " and date(time)>='" + filters.get("fromdate") + \
        "' and date(time)<='" + filters.get("todate") + "' group by date(time)"
    # frappe.utils.data.formatdate(filters.get("todate"),"dd-mm-yyyy")
    #conditions += " and date(time)>='2020-06-01' and date(time)<='2020-06-28'"  + " group by date(time)"

    return conditions