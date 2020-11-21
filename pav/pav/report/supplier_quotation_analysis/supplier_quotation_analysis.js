frappe.query_reports['Supplier Quotation Analysis'] = {
    filters: [
        {
            fieldname: 'rfq',
            label: __('Request for Quotation'),
            fieldtype: 'Link',
            "options": 'Request for Quotation',
	    "reqd": 1      
	}
	]
}