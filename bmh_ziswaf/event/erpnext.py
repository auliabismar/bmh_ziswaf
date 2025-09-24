import frappe

def cost_center_after_rename(doc, method=None, old_name=None, new_name=None, merge=False):
  if not doc.is_group:
    old_parts = old_name.split(" - ")
    new_parts = new_name.split(" - ")
    old_cost_center_number = old_parts[0] if len(old_parts) > 0 else ""
    old_cost_center_name = old_parts[1] if len(old_parts) > 1 else ""
    new_cost_center_number = new_parts[0] if len(new_parts) > 0 else ""
    new_cost_center_name = new_parts[1] if len(new_parts) > 1 else ""
    if old_cost_center_name != new_cost_center_name:
      frappe.rename_doc('Branch', old_cost_center_name, new_cost_center_name)
      frappe.rename_doc('Location', old_cost_center_name, new_cost_center_name)
    if old_cost_center_number != new_cost_center_number:
      frappe.db.set_value('Branch', new_cost_center_name, 'custom_prefix', new_cost_center_number[:3])
      frappe.db.set_value('Location', new_cost_center_name, 'custom_prefix', new_cost_center_number[:3])

def cost_center_after_insert(doc, method=None):
  if doc.is_group == '0':
    branch = frappe.new_doc('Branch')
    branch.branch = doc.cost_center_name
    branch.custom_cost_center = doc.name
    if doc.cost_center_number:
      branch.custom_cost_center_no = doc.cost_center_number
      branch.custom_prefix = doc.cost_center_number[:3]
    branch.insert(ignore_permissions=True)
    location = frappe.new_doc('Location')
    location.location_name = doc.cost_center_name
    location.custom_cost_center = doc.name
    if doc.cost_center_number:
      location.custom_prefix = doc.cost_center_number[:3]
    location.insert(ignore_permissions=True)
  supplier = frappe.new_doc('Supplier')
  supplier.name = doc.cost_center_number
  supplier.supplier_name = doc.cost_center_name
  supplier.supplier_type = 'Partnership'
  supplier.db_insert()
  customer = frappe.new_doc('Customer')
  customer.name = doc.cost_center_number
  customer.customer_name = doc.cost_center_name
  customer.customer_type = 'Partnership'
  customer.db_insert()

def cost_center_after_delete(doc, method=None):
  if not doc.is_group:
    frappe.delete_doc('Branch', doc.cost_center_name, ignore_missing=True, force=True)
    frappe.delete_doc('Location', doc.cost_center_name, ignore_missing=True, force=True)
  frappe.delete_doc('Supplier', doc.cost_center_number, ignore_missing=True, force=True)
  frappe.delete_doc('Customer', doc.cost_center_number, ignore_missing=True, force=True)

def asset_before_insert(doc, method=None):
  if doc.available_for_use_date:
    doc.custom_available_year = frappe.utils.getdate(doc.available_for_use_date).year

def project_type_autoname(doc, method=None):
  series_key = f".{doc.custom_abbreviation}.-.##"
  new_name = frappe.model.naming.make_autoname(series_key, doc)
  doc.name = new_name

def project_autoname(doc, method=None):
  series_key = f".{doc.project_type}.-.##"
  new_name = frappe.model.naming.make_autoname(series_key, doc)
  doc.name = new_name

def journal_entry_on_cancel(doc, method):
	donation = frappe.get_value(
		"Donation", {"journal_entry": doc.name}, "name")
	if donation:
		donation_doc = frappe.get_doc("Donation", donation)
		if donation_doc.docstatus != 2:
			donation_doc.cancel()