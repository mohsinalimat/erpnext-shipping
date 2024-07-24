# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
import requests
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from frappe.utils.data import get_link_to_form
from requests.exceptions import HTTPError

from erpnext_shipping.erpnext_shipping.utils import show_error_alert

SENDCLOUD_PROVIDER = "SendCloud"
WEIGHT_DECIMALS = 3
CURRENCY_DECIMALS = 2

class SendCloud(Document):
	pass


class SendCloudUtils:
	def __init__(self):
		settings = frappe.get_single("SendCloud")
		self.api_key = settings.api_key
		self.api_secret = settings.get_password("api_secret")
		self.enabled = settings.enabled

		if not self.enabled:
			link = get_link_to_form("SendCloud", "SendCloud", _("SendCloud Settings"))
			frappe.throw(_("Please enable SendCloud Integration in {0}").format(link))

	def get_available_services(self, delivery_address, parcels: list[dict]):
		# Retrieve rates at SendCloud from specification stated.
		if not self.enabled or not self.api_key or not self.api_secret:
			return []

		to_country = delivery_address.country_code.upper()

		try:
			response = requests.get(
				"https://panel.sendcloud.sc/api/v2/shipping_methods",
				params={
					"to_country": to_country,
				},
				auth=(self.api_key, self.api_secret),
			)
			responses_dict = response.json()

			if "error" in responses_dict:
				error_message = responses_dict["error"]["message"]
				frappe.throw(error_message, title=_("SendCloud"))

			available_services = []
			for service in responses_dict.get("shipping_methods", []):
				countries = [
					country
					for country in service["countries"]
					if country["iso_2"] == to_country
				]

				if countries and check_weight(service, parcels):
					available_service = self.get_service_dict(
						service, countries[0], parcels
					)
					available_services.append(available_service)

			return available_services
		except Exception:
			show_error_alert("fetching SendCloud prices")

	def create_shipment(
		self,
		shipment,
		delivery_company_name,
		delivery_address,
		delivery_contact,
		service_info,
		shipment_parcel,
		description_of_content,
		value_of_goods,
	):
		# Create a transaction at SendCloud
		if not self.enabled or not self.api_key or not self.api_secret:
			return []

		parcels = []
		for i, parcel in enumerate(json.loads(shipment_parcel), start=1):
			parcel_data = self.get_parcel_dict(
				shipment,
				parcel,
				i,
				delivery_company_name,
				delivery_address,
				delivery_contact,
				service_info,
				description_of_content,
				value_of_goods,
			)
			parcels.append(parcel_data)

		try:
			response = requests.post(
				"https://panel.sendcloud.sc/api/v2/parcels?errors=verbose",
				json={"parcels": parcels},
				auth=(self.api_key, self.api_secret),
			)
			response_data = response.json()
			if "failed_parcels" in response_data:
				error = response_data["failed_parcels"][0]["errors"]
				frappe.msgprint(
					_("Error occurred while creating Shipment: {0}").format(error),
					indicator="orange",
					alert=True,
				)
			else:
				shipment_id = ", ".join([str(x["id"]) for x in response_data["parcels"]])
				awb_number = ", ".join([str(x["tracking_number"]) for x in response_data["parcels"]])
				return {
					"service_provider": "SendCloud",
					"shipment_id": shipment_id,
					"carrier": self.get_carrier(service_info["carrier"], post_or_get="post"),
					"carrier_service": service_info["service_name"],
					"shipment_amount": service_info["total_price"],
					"awb_number": awb_number,
				}
		except Exception:
			show_error_alert("creating SendCloud Shipment")

	def get_label(self, shipment_id):
		# Retrieve shipment label from SendCloud
		shipment_id_list = shipment_id.split(", ")
		label_urls = []

		try:
			for ship_id in shipment_id_list:
				shipment_label_response = requests.get(
					f"https://panel.sendcloud.sc/api/v2/labels/{ship_id}",
					auth=(self.api_key, self.api_secret),
				)
				shipment_label = json.loads(shipment_label_response.text)
				label_urls.append(shipment_label["label"]["label_printer"])
			if len(label_urls):
				return label_urls
			else:
				message = _(
					"Please make sure Shipment (ID: {0}), exists and is a complete Shipment on SendCloud."
				).format(shipment_id)
				frappe.msgprint(msg=_(message), title=_("Label Not Found"))
		except Exception:
			show_error_alert("printing SendCloud Label")

	def download_label(self, label_url: str):
		"""Download label from SendCloud."""
		try:
			resp = requests.get(label_url, auth=(self.api_key, self.api_secret))
			resp.raise_for_status()
			return resp.content
		except HTTPError:
			frappe.msgprint(
				_("An error occurred while downloading label from SendCloud"), indicator="orange", alert=True
			)

	def get_tracking_data(self, shipment_id):
		# return SendCloud tracking data
		try:
			shipment_id_list = shipment_id.split(", ")
			awb_number, tracking_status, tracking_status_info, tracking_urls = [], [], [], []

			for ship_id in shipment_id_list:
				tracking_data_response = requests.get(
					f"https://panel.sendcloud.sc/api/v2/parcels/{ship_id}",
					auth=(self.api_key, self.api_secret),
				)
				tracking_data = json.loads(tracking_data_response.text)
				tracking_data_parcel = tracking_data["parcel"]
				tracking_data_parcel_status = tracking_data_parcel["status"]["message"]

				tracking_urls.append(tracking_data_parcel["tracking_url"])
				awb_number.append(tracking_data_parcel["tracking_number"])
				tracking_status.append(tracking_data_parcel_status)
				tracking_status_info.append(tracking_data_parcel_status)
			return {
				"awb_number": ", ".join(awb_number),
				"tracking_status": ", ".join(tracking_status),
				"tracking_status_info": ", ".join(tracking_status_info),
				"tracking_url": ", ".join(tracking_urls),
			}
		except Exception:
			show_error_alert("updating SendCloud Shipment")

	def total_parcel_price(self, parcel_price, parcels: list[dict]):
		count = 0
		for parcel in parcels:
			count += parcel.get("count")
		return flt(parcel_price) * count

	def get_parcel_items(self, parcel, description_of_content, value_of_goods):
		parcel_list = []
		formatted_parcel = {}
		formatted_parcel["description"] = description_of_content
		formatted_parcel["quantity"] = parcel.get("count")
		formatted_parcel["weight"] = flt(parcel.get("weight"), WEIGHT_DECIMALS)
		formatted_parcel["value"] = flt(value_of_goods, CURRENCY_DECIMALS)
		parcel_list.append(formatted_parcel)
		return parcel_list

	def get_service_dict(self, service, country, parcels: list[dict]):
		"""Returns a dictionary with service info."""
		available_service = frappe._dict()
		available_service.service_provider = "SendCloud"
		available_service.carrier = self.get_carrier(service["carrier"], post_or_get="get")
		available_service.service_name = service["name"]

		price = country["price"] or sum(price_part["value"] for price_part in country["price_breakdown"])
		available_service.total_price = self.total_parcel_price(price, parcels)

		available_service.service_id = service["id"]

		return available_service

	def get_carrier(self, carrier_name, post_or_get=None):
		# make 'sendcloud' => 'SendCloud' while displaying rates
		# reverse the same while creating shipment
		if carrier_name in ("sendcloud", "SendCloud"):
			return "SendCloud" if post_or_get == "get" else "sendcloud"
		else:
			return carrier_name.upper() if post_or_get == "get" else carrier_name.lower()

	def get_parcel_dict(
		self,
		shipment,
		parcel,
		index,
		delivery_company_name,
		delivery_address,
		delivery_contact,
		service_info,
		description_of_content,
		value_of_goods,
	):
		return {
			"name": f"{delivery_contact.first_name} {delivery_contact.last_name}",
			"company_name": delivery_company_name or delivery_address.address_title,
			"address": delivery_address.address_line1,
			"address_2": delivery_address.address_line2 or "",
			"city": delivery_address.city,
			"postal_code": delivery_address.pincode,
			"telephone": delivery_contact.phone,
			"request_label": True,
			"email": delivery_contact.email_id,
			"data": [],
			"country": delivery_address.country_code.upper(),
			"shipment": {"id": service_info["service_id"]},
			"order_number": f"{shipment}-{index}",
			"external_reference": f"{shipment}-{index}",
			"weight": flt(parcel.get("weight"), WEIGHT_DECIMALS),
			"parcel_items": self.get_parcel_items(parcel, description_of_content, value_of_goods),
		}


def check_weight(service: dict, parcels: list[dict]) -> bool:
	"""Check if the weight of any parcel is within the range of the service."""
	max_weight_kg = float(service["max_weight"])
	min_weight_kg = float(service["min_weight"])
	return any(
		max_weight_kg > parcel.get("weight") and min_weight_kg <= parcel.get("weight")
		for parcel in parcels
	)
