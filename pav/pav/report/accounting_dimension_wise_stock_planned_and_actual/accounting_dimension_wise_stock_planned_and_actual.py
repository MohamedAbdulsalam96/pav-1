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
        # add = []
        # for d in dimensions:
        #     lft, rgt = frappe.db.get_value(filters.get("budget_against"), d, ["lft", "rgt"])
        #     add += """
        #             select
        #                 name
        #             from
        #                 `tab{tab}` where lft>=%s and rgt<=%s and docstatus<2
        #         """.format(tab=filters.get("budget_against")) % (lft, rgt)
                
        # dimensions += add

    else:
        dimensions = get_cost_centers(filters)

    dimension_target_details = get_dimension_target_details(
        dimensions, filters)
    # frappe.msgprint("{0}".format(dimension_target_details))
    for ccd in dimension_target_details:
        if not ccd.actual_qty:
            ccd.actual_qty = 0
        if not ccd.planned_qty:
            ccd.planned_qty = 0
        
        sum = 0
        if ccd.planned_qty != 0:
           sum = (ccd.planned_qty-ccd.actual_qty)/ccd.planned_qty*100
        
        if filters.get("budget_against")=="Task":
            data.append([ccd.budget_against, ccd.budget_against_name, ccd.project, ccd.item_code, ccd.item_name, ccd.planned_qty,
                     ccd.actual_qty, (ccd.planned_qty-ccd.actual_qty), sum])
        else:
            data.append([ccd.budget_against, ccd.budget_against_name, ccd.item_code, ccd.item_name, ccd.planned_qty,
                     ccd.actual_qty, (ccd.planned_qty-ccd.actual_qty), sum])
    return columns, data


def get_columns(filters):
    columns = [
		_(filters.get("budget_against")) + ":Link/%s:120" % (filters.get("budget_against"))		
	]
    if filters.budget_against == "Task":
        columns.append(_("Subject") + ":Data:200")
        columns.append(_("Project") + ":Link/Project:100")		
    else:
        columns.append(_(filters.get("budget_against")+" Name") + ":Data:200")
    
    columns.append(_('Item') + ":Link/Item:150")
    columns.append(_('Item Name') + ":Data:150")

    if filters["value_quantity"] == 'Value':
        columns.append("Planned Amount:Float:100")
        columns.append("Actual Amount:Float:100")
        #columns.append("Variance Qty:Float:100")
        columns.append({
            "fieldname": "variance_qty",
            "label": _("Variance Amount"),
            "fieldtype": "Float",
            "width": 100
        })
    else:
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
    
    if ((filters.budget_against == "Task" or filters.budget_against == "Property" ) and filters.get('project')):
        cond += """and bal.project = %s""" % (frappe.db.escape(filters.get('project')))

    if dimensions:
        cond += """ and mri.{budget_against} in (%s)""".format(
                budget_against=budget_against) % ", ".join(["%s"] * len(dimensions))
        dimensions += dimensions
    
    col = ""
    col2 = ""
    if filters.budget_against == "Task":
        col= """ bal.project as project, bal.subject """
        col2= """ project , budget_against_name """
    else:
        col = """ bal.%s_name """ % (budget_against)
        col2 = """ budget_against_name """

    
    if filters["value_quantity"] == 'Value':
        value_field = 'amount'
    else:
        value_field = 'qty'

    v = frappe.db.sql(
        """
        select
                budget_against,
				item_name,
                item_code,
                name,
                bal_name,
                {col2},
				 sum(planned_qty)  as planned_qty,
				 sum(actual_qty)  as actual_qty
                from
			(
                select
                mri.{budget_against} as budget_against,
				i.item_name as item_name,
                i.item_code as item_code,
                i.name as name,
                bal.name as bal_name,
                {col} as budget_against_name,
                
				sum(mri.{value_field}) as planned_qty,
				0 as actual_qty
			from				
			    `tabMaterial Request Item` mri 
                INNER JOIN `tabItem` i on mri.item_code = i.name
                INNER JOIN `tab{budget_against_label}` bal on mri.{budget_against} = bal.name
                INNER JOIN `tabMaterial Request` mr on mri.parent=mr.name 
            where
             i.is_stock_item=1 and mr.company = {company}
			and mr.transaction_date between {from_date} and {to_date}
            {cond}
            group by
				i.name, bal.name

            UNION 

            select
                mri.{budget_against} as budget_against,
				i.item_name as item_name,
                i.item_code as item_code,
                i.name as name,
                bal.name as bal_name,
                {col} as budget_against_name,
                
				0 as planned_qty,
				sum(mri.{value_field}) as actual_qty
			from				
			    `tabStock Entry Detail` mri 
                INNER JOIN `tabItem` i on mri.item_code = i.name 
                INNER JOIN `tab{budget_against_label}` bal on mri.{budget_against} = bal.name
                INNER JOIN `tabStock Entry` mr on mri.parent=mr.name 
                
			where
             i.is_stock_item=1 and mr.company = {company}
			and mr.posting_date between {from_date} and {to_date}
            {cond}
            group by
				i.name, bal.name
            ) q
			group by
				name, bal_name
		""".format(
            value_field=value_field,
            budget_against_label=filters.budget_against,
            company = frappe.db.escape(filters.company),
            from_date = frappe.db.escape(filters.from_date),
            to_date = frappe.db.escape(filters.to_date),
            budget_against=budget_against,
            cond=cond,
            col = col,
            col2 = col2,
        ), tuple(dimensions), as_dict=True)
    return v
   
    # return frappe.db.sql(
    #     """
	# 		select
	# 			mri.{budget_against} as budget_against,
	# 			bal.{budget_against}_name as budget_against_name,
	# 			mri.item_code,
	# 			i.item_name as item_name,
	# 			sum(mri.{value_field}) as planned_qty,
	# 			(select IFNULL(sum(sei.{value_field}) ,0)
	# 				from `tabStock Entry Detail` sei 
	# 				INNER JOIN `tabStock Entry` se on sei.parent=se.name		
	# 				where sei.item_code=mri.item_code
	# 				and sei.{budget_against}=mri.{budget_against}
	# 				and se.purpose='Material Issue'
	# 				and se.docstatus=1
	# 			) as actual_qty
	# 		from
	# 			`tabMaterial Request Item` mri
	# 			INNER JOIN `tabMaterial Request` mr on mri.parent=mr.name
	# 			INNER JOIN `tabItem` i on i.name=mri.item_code
	# 			INNER JOIN `tab{budget_against_label}` bal on mri.{budget_against}=bal.name
	# 		where
	# 			i.is_stock_item=1
	# 			and mr.material_request_type='Material Issue'
	# 			and mr.docstatus=1
	# 			and mr.company = %s 
	# 			and mr.transaction_date between %s and %s 
	# 			{cond}
	# 		group by
	# 			mri.item_code, mri.{budget_against}
	# 	""".format(
    #         value_field=value_field,
    #         budget_against_label=filters.budget_against,
    #         budget_against=budget_against,
    #         cond=cond,
    #     ),
    #     tuple(
    #         [
    #             filters.company,
    #             filters.from_date,
    #             filters.to_date
    #         ]
    #         + dimensions
    #     ), as_dict=True)
