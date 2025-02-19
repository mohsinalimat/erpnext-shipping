from . import __version__ as app_version

app_name = "erpnext_shipping"
app_title = "ERPNext Shipping"
app_publisher = "Frappe"
app_description = "A Shipping Integration fir ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "developers@frappe.io"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/erpnext_shipping/css/erpnext_shipping.css"
app_include_js = "shipping.bundle.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpnext_shipping/css/erpnext_shipping.css"
# web_include_js = "/assets/erpnext_shipping/js/erpnext_shipping.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpnext_shipping/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Shipment": "public/js/shipment.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "erpnext_shipping.install.before_install"
after_install = "erpnext_shipping.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_shipping.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# }
# }

# Scheduled Tasks
# ---------------

scheduler_events = {"daily": ["erpnext_shipping.erpnext_shipping.utils.update_tracking_info_daily"]}

# Testing
# -------

# before_tests = "erpnext_shipping.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "erpnext_shipping.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "erpnext_shipping.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

shipping_custom_fields = {
	"Delivery Note": [
		{
			"fieldname": "shipping_sec_break",
			"label": "Shipping Details",
			"fieldtype": "Section Break",
			"collapsible": 1,
			"insert_after": "sales_team",
		},
		{
			"fieldname": "delivery_type",
			"label": "Delivery Type",
			"fieldtype": "Data",
			"read_only": 1,
			"translatable": 0,
			"insert_after": "shipping_sec_break",
		},
		{
			"fieldname": "parcel_service",
			"label": "Parcel Service",
			"fieldtype": "Data",  # needs to be "Data" for backward compat
			"options": "Parcel Service",
			"read_only": 1,
			"insert_after": "delivery_type",
		},
		{
			"fieldname": "parcel_service_type",
			"label": "Parcel Service Type",
			"fieldtype": "Data",  # needs to be "Data" for backward compat
			"options": "Parcel Service Type",
			"read_only": 1,
			"insert_after": "parcel_service",
		},
		{
			"fieldname": "shipping_col_break",
			"fieldtype": "Column Break",
			"insert_after": "parcel_service_type",
		},
		{
			"fieldname": "tracking_number",
			"label": "Tracking Number",
			"fieldtype": "Data",
			"read_only": 1,
			"translatable": 0,
			"insert_after": "shipping_col_break",
		},
		{
			"fieldname": "tracking_url",
			"label": "Tracking URL",
			"fieldtype": "Small Text",
			"read_only": 1,
			"translatable": 0,
			"insert_after": "tracking_number",
		},
		{
			"fieldname": "tracking_status",
			"label": "Tracking Status",
			"fieldtype": "Data",
			"read_only": 1,
			"translatable": 0,
			"insert_after": "tracking_url",
		},
		{
			"fieldname": "tracking_status_info",
			"label": "Tracking Status Information",
			"fieldtype": "Data",
			"read_only": 1,
			"translatable": 0,
			"insert_after": "tracking_status",
		},
	]
}

doc_events = {
	"Shipment": {
		"validate": [
			"erpnext_shipping.erpnext_shipping.utils.validate_parcels",
			"erpnext_shipping.erpnext_shipping.utils.validate_phone",
		]
	},
}
