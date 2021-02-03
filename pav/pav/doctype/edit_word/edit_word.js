// Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
// For license information, please see license.txt

frappe.ui.form.on('edit word', {
	// refresh: function(frm) {

	// }
	after_save(frm){
		var dialog = new frappe.ui.Dialog({
			title: __('Choose a template file'),
			fields: [
				{
					fieldname: 'template',
					fieldtype: 'Link',
					label: 'File',
					options: 'File'
				},
			],
			primary_action: () => {
				dialog.hide();
				frappe.call({
					method: "pav.pav.doctype.edit_word.edit_word.fill_and_attach_template",
					args: {
						doctype: frm.doc.doctype,
						name: frm.doc.name,
						template: dialog.get_values().template,
					},
					callback: (r) => frm.reload_doc(),
				});
			}
		});
		dialog.show();
	}
});
