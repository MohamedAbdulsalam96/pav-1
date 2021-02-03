## PAV

Partner Added Value

Requirments for project activities:-
#1.Custom fields in Project
1.1.Is Program -> Check -> is_program
1.2.Project Title -> Data -> project_title (Mandatory,Unique)

#2.Custom Script for project
this.frm.dashboard.add_transactions([
	{	    
		'items': [
			'Budget',
			'Project Activities'
		],
		'label': 'Budget & Project Activities'
	}	
]);

#3.Server Script for project - before insert
if doc.is_program==1:
    frappe.get_doc(dict(
            doctype = 'Project Dimension',
            project_code = doc.name,
            status = doc.status,
            project_code = doc.name
        )).insert()

#Ignore #3

#### License

#.Edit code:erpnext->controllers->accounts_controller.py
Add:"Expense Entry" in this condition -> if gl_dict.account and self.doctype not in ["Journal Entry","Period Closing Voucher", "Payment Entry", "Expense Entry"]:

MIT
