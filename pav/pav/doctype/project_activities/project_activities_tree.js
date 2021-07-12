frappe.provide("frappe.treeview_settings");

frappe.treeview_settings['Project Activities'] = {
	get_tree_nodes: "pav.pav.doctype.project_activities.project_activities.get_children",
	add_tree_node:  "pav.pav.doctype.project_activities.project_activities.add_node",
	filters: [
		{
			fieldname: "company",
			fieldtype:"Select",
			options: erpnext.utils.get_tree_options("company"),
			label: __("Company"),
			default: erpnext.utils.get_tree_default("company"),
		},
		{
			fieldname: "project",
			fieldtype:"Link",
			options: "Project",
			label: __("Project"),
		},
		{
			fieldname: "project_activities",
			fieldtype:"Link",
			options: "Project Activities",
			label: __("Project Activities"),
			get_query: function() {
				var me = frappe.treeview_settings['Project Activities'];
				var project = me.page.fields_dict.project.get_value();
				var args = [["Project Activities", 'is_group', '=', 1]];
				if(project){
					args.push(["Project Activities", 'project', "=", project]);
				}
				return {
					filters: args
				};
			}
		}
	],
	breadcrumb: "Projects",
	get_tree_root: false,
	root_label: "All Project Activities",
	ignore_fields: ["parent_project_activities"],
	onload: function(me) {
		frappe.treeview_settings['Project Activities'].page = {};
		$.extend(frappe.treeview_settings['Project Activities'].page, me.page);
		me.make_tree();
	},
	onrender: function(node) {
		console.log('kkk')
		if(frappe.boot.user.can_read.indexOf("GL Entry") !== -1){
			
			// show Dr if positive since balance is calculated as debit - credit else show Cr
			let balance = node.data.balance;
			let dr_or_cr = balance > 0 ? "Dr": "Cr";

			if (node.data && node.data.balance!==undefined) {
				$('<span class="balance-area pull-right text-muted small">'
					+ format_currency(Math.abs(node.data.balance), node.data.company_currency)
					+ " " + dr_or_cr
					+ '</span>').insertBefore(node.$ul);
			}
		}
	},
	toolbar: [
		{
			label:__("Add Multiple"),
			condition: function(node) {
				return node.expandable;
			},
			click: function(node) {
				this.data = [];
				const dialog = new frappe.ui.Dialog({
					title: __("Add Multiple Project Activities"),
					fields: [
						{
							fieldname: "multiple_project_activities", fieldtype: "Table",
							in_place_edit: true, data: this.data,
							get_data: () => {
								return this.data;
							},
							fields: [{
								fieldtype:'Data',
								fieldname:"project_activity",
								in_list_view: 1,
								reqd: 1,
								label: __("Project Activity")
							}]
						},
					],
					primary_action: function() {
						dialog.hide();
						return frappe.call({
							method: "pav.pav.doctype.project_activities.project_activities.add_multiple_project_activities",
							args: {
								data: dialog.get_values()["multiple_project_activities"],
								parent: node.data.value
							},
							callback: function() { }
						});
					},
					primary_action_label: __('Create')
				});
				dialog.show();
			}
		}
	],
	extend_toolbar: true
};