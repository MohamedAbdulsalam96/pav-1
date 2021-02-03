# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed Mohammed Alkuhlani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from six import BytesIO


class editword(Document):
	pass

def _fill_template(template, data):
	if data:
		from docxtpl import DocxTemplate
		doc = DocxTemplate(template)
		doc.render(data)
		_file = BytesIO()
		doc.docx.save(_file)
		return _file
	return None

@frappe.whitelist()
def fill_and_attach_template(doctype, name, template):
    """
    Use a documents data to fill a docx template and attach the result.

    Reads a document and a template file, fills the template with data from the
    document and attaches the resulting file to the document.

    :param doctype"     data doctype
    :param name"        data name
    :param template"    name of the template file
    """
    data = frappe.get_doc(doctype, name)
    data_dict = data.as_dict()

    template_doc = frappe.get_doc("File", template)
    template_path = template_doc.get_full_path()

    output_file = _fill_template(template_path, data_dict)
    output_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": "-".join([name, template_doc.file_name]),
        "attached_to_doctype": doctype,
        "attached_to_name": name,
        "content": output_file.getvalue(),
    })
    output_doc.save()