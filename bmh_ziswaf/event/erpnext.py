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
				 
def payment_entry_before_submit(doc, method):
	is_bank_involved = (doc.paid_from_account_type == 'Bank' or doc.paid_to_account_type == 'Bank')
	needs_reference = is_bank_involved and doc.paid_from and doc.paid_to
	has_incomplete_ref = not doc.reference_no or not doc.reference_date
	if needs_reference and has_incomplete_ref:
		frappe.throw("Reference No and Reference Date are required for Payment Entry with Bank Account.")

def employee_advance_on_submit(doc, method):
	account = frappe.db.get_value('Mode of Payment Account', 
		{'parent': doc.mode_of_payment, 'company': doc.company}, 'default_account')
	bank_account = frappe.db.get_value('Bank Account', 
		{'account': account, 'company': doc.company, 'disabled': 0}, 'name')
	party_bank_account = frappe.db.get_value('Bank Account', 
		{'party_type': 'Employee', 'party': doc.employee, 'disabled': 0}, 'name')
	pe = frappe.new_doc('Payment Entry')
	pe.payment_type = 'Pay'
	pe.company = doc.company
	pe.cost_center = doc.custom_cost_center
	pe.akad = doc.custom_akad
	pe.project = doc.custom_project
	pe.posting_date = frappe.utils.nowdate()
	pe.mode_of_payment = doc.mode_of_payment
	pe.party_type = 'Employee'
	pe.party = doc.employee
	pe.contact_email = frappe.db.get_value('Employee', doc.employee, 'prefered_email')
	pe.paid_from = account
	pe.paid_to = doc.advance_account
	pe.paid_from_account_currency = 'IDR'
	pe.paid_to_account_currency = 'IDR'
	pe.paid_amount = doc.advance_amount
	pe.received_amount = doc.advance_amount - doc.paid_amount
	pe.append('references', {
		'reference_doctype': 'Employee Advance',
		'reference_name': doc.name,
		'total_amount': doc.advance_amount,
		'allocated_amount': doc.advance_amount - doc.paid_amount,
		'outstanding_amount': doc.advance_amount - doc.paid_amount,
	})
	pe.party_name = frappe.db.get_value(pe.party_type, pe.party, 'employee_name')
	pe.paid_from_account_type = frappe.get_cached_value('Account', account, 'account_type')
	pe.paid_to_account_type = frappe.get_cached_value('Account', doc.advance_account, 'account_type')
	pe.total_allocated_amount = abs(doc.advance_amount)
	pe.bank_account = bank_account if bank_account else None
	pe.party_bank_account = party_bank_account if party_bank_account else None
	pe.save()
	frappe.msgprint(
		msg=f'Payment Entry {pe.name} created for Employee Advance {doc.name}.',
		title='Auto Create Payment Entry',
		indicator='green',
		primary_action={
			'label': 'View Payment Entry',
			'client_action': 'frappe.set_route',
			'args': ['Form', 'Payment Entry', pe.name],
		}
	)