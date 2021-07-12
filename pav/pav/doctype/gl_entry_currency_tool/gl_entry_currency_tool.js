// Copyright (c) 2021, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt

frappe.ui.form.on('GL Entry Currency Tool', {
	start: function(frm) {
		return frappe.call({
			doc: frm.doc,
			method: 'update_gl_entry',
			callback: function(r) {				
			}
		})
	}
});
