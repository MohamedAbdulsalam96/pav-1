import frappe
from frappe import _
from frappe.utils import cstr

def execute(filters=None):
	if not filters: filters = {}
	columns = get_columns()
	sup_map = get_supplier(filters)
	count=0
	for supplier in sorted(sup_map):
		count+=1
		columns.append({
			"fieldname": "supplier"+cstr(count),
			"label": supplier,
			"fieldtype": "Float",
			"width": 150
		})

	data = []
	item_map = get_item(filters)
	qtys=0.0
	sups={}
	count=0
	for item in item_map:
		count=0
		item_det = item_map.get(item)

		if not item_det:
			continue

		row = [item_det.item_code, item_det.item_name, item_det.qty]
		qtys+=item_det.qty
		for supplier in sorted(sup_map):
			count+=1
			supplier_det = sup_map.get(supplier)
			if not supplier_det:
				continue
			if not sups.get(count):
				sups[count]={}
			sq=frappe.db.sql("""SELECT sq.name FROM `tabSupplier Quotation` sq 
				INNER JOIN `tabSupplier Quotation Item` sqi on sqi.parent=sq.name
				where sq.supplier =%(supplier)s
				and sqi.request_for_quotation=%(rfq)s
				and sq.docstatus=1 and sqi.docstatus=1""",
				{"supplier":supplier_det.supplier,
				"rfq":filters["rfq"]})
			if sq:
				rate_amount=frappe.db.sql("""SELECT IFNULL(rate,0.0),IFNULL(amount,0.0),IFNULL(qty,0.0) FROM 
					`tabSupplier Quotation Item` where 
					item_code=%(item_code)s
					and parent=%(parent)s
					and request_for_quotation_item=%(rfqi)s and docstatus=1""",
					{"item_code":item_det.item_code,"parent":sq[0][0],"rfqi":item_det.name})
				if rate_amount:
					row.extend([rate_amount[0][0] if rate_amount[0][0] else None])
					sups[count]["total"]=sups[count].get("total",0.0)+(rate_amount[0][1])
				else:
					row.extend([None])
			else:
				row.extend([None])
		data.append(row)

	total = ["", "Total:", qtys if qtys else None]
	for tot in sorted(sups):
		total.extend([sups[tot].get("total",0.0)])
	data.append(total)

	rfqd=frappe.db.sql("""SELECT approved_supplier_quotation, approved_supplier, interpretation_of_accreditation FROM `tabRequest for Quotation` where name =%(rfq)s
		""",{"rfq":filters["rfq"]})

	row = {
		"approved_supplier_quotation": rfqd[0][0],
		"approved_supplier": rfqd[0][1],
		"interpretation_of_accreditation": rfqd[0][2]
	}
	data.append(row)

	return columns, data

def get_columns():
	return [
		{
			"fieldname": "item",
			"label": _("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 100
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "qty",
			"label": _("QTY"),
			"fieldtype": "Float",
			"width": 100
		}
	]

def get_item(filters):
	item_map = frappe._dict()
	item_list = frappe.db.sql("""SELECT name, item_code, item_name, uom, qty FROM `tabRequest for Quotation Item` where parent=%(rfq)s and docstatus=1 order by idx asc""",{"rfq":filters["rfq"]}, as_dict=1)
	for item in item_list:
		if item :
			item_map.setdefault(item.name, item)

	return item_map

def get_supplier(filters):
	sup_map = frappe._dict()
	sup_list = frappe.db.sql("""SELECT supplier FROM `tabRequest for Quotation Supplier` where parent=%(rfq)s and docstatus=1""",{"rfq":filters["rfq"]}, as_dict=1)
	for sup in sup_list:
		if sup :
			sup_map.setdefault(sup.supplier, sup)


	return sup_map



