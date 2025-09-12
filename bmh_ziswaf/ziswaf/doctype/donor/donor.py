# Copyright (c) 2025, PT Karya Tata Bangsa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.contacts.address_and_contact import (load_address_and_contact, delete_contact_and_address)

class Donor(Document):
	def onload(self):
		load_address_and_contact(self)
	
	def on_trash(self):
		delete_contact_and_address(self.doctype, self.name)
