# Copyright (c) 2020, Frappe Technologies and contributors
# For license information, please see license.txt
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_fields = frappe.get_hooks("shipping_custom_fields")
	create_custom_fields(custom_fields)
