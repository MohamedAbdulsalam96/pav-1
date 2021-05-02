# Copyright (c) 2013, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, formatdate


def execute(filters=None):
    if not filters:
        filters = {}
    columns, data = [], []
    columns = get_columns(filters)
    if filters.get("budget_against_filter"):
        dimensions = filters.get("budget_against_filter")
    else:
        dimensions = get_cost_centers(filters)

    dimension_target_details = get_dimension_target_details(
        dimensions, filters)
    # frappe.msgprint("{0}".format(dimension_target_details))
    for ccd in dimension_target_details:
        data.append([ccd.budget_against, ccd.budget_against_name, ccd.item_code, ccd.item_name, ccd.planned_qty,
                     ccd.actual_qty, (ccd.planned_qty-ccd.actual_qty), (ccd.planned_qty-ccd.actual_qty)/ccd.planned_qty*100])

    return columns, data


def get_columns(filters):
    columns = [
        _(filters.get("budget_against")) + ":Link/%s:150" % (filters.get("budget_against")),
        _(filters.get("budget_against")+" Name") + ":Data:150",
        _('Item') + ":Link/Item:150",
        _('Item Name') + ":Data:150"
    ]
    columns.append("Planned Qty:Float:100")
    columns.append("Actual Qty:Float:100")
    #columns.append("Variance Qty:Float:100")
    columns.append({
        "fieldname": "variance_qty",
        "label": _("Variance Qty"),
        "fieldtype": "Float",
        "width": 100
    })
    columns.append("Variance %:Float:100")
    return columns


def get_cost_centers(filters):
    order_by = ""
    if filters.get("budget_against") == "Cost Center":
        order_by = "order by lft"

    if filters.get("budget_against") in ["Cost Center", "Project"]:
        return frappe.db.sql_list(
            """
				select
					name
				from
					`tab{tab}`
				where
					company = %s
				{order_by}
			""".format(tab=filters.get("budget_against"), order_by=order_by),
            filters.get("company"))
    else:
        return frappe.db.sql_list(
                """
				select
					name
				from
					`tab{tab}`
			""".format(tab=filters.get("budget_against")))  # nosec


def get_dimension_target_details(dimensions, filters):
    budget_against = frappe.scrub(filters.get("budget_against"))
    cond = ""
    if dimensions:
        cond += """ and mri.{budget_against} in (%s)""".format(
                budget_against=budget_against) % ", ".join(["%s"] * len(dimensions))

    return frappe.db.sql(
        """
			select
				mri.{budget_against} as budget_against,
				bal.{budget_against}_name as budget_against_name,
				mri.item_code,
				i.item_name as item_name,
				sum(mri.stock_qty) as planned_qty,
				(select IFNULL(sum(sei.transfer_qty) ,0)
					from `tabStock Entry Detail` sei 
					INNER JOIN `tabStock Entry` se on sei.parent=se.name					
					where sei.item_code=mri.item_code
					and sei.{budget_against}=mri.{budget_against}
					and se.purpose='Material Issue'
					and se.docstatus=1
				) as actual_qty
			from
				`tabMaterial Request Item` mri
				INNER JOIN `tabMaterial Request` mr on mri.parent=mr.name
				INNER JOIN `tabItem` i on i.name=mri.item_code
				INNER JOIN `tab{budget_against_label}` bal on mri.{budget_against}=bal.name
			where
				i.is_stock_item=1
				and mr.material_request_type='Material Issue'
				and mr.docstatus=1
				and mr.company = %s 
				and mr.transaction_date between %s and %s 
				{cond}
			group by
				mri.item_code, mri.{budget_against}
		""".format(
            budget_against_label=filters.budget_against,
            budget_against=budget_against,
            cond=cond,
        ),
        tuple(
            [
                filters.company,
                filters.from_date,
                filters.to_date
            ]
            + dimensions
        ), as_dict=True)
