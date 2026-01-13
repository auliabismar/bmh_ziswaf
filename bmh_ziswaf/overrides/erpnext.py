import frappe
from frappe.utils import nowdate
from hrms.overrides.employee_payment_entry import (
    get_party_account,
    get_account_currency,
    get_grand_total_and_outstanding_amount,
    get_bank_cash_account,
    get_paid_amount_and_received_amount,
)

@frappe.whitelist()
def get_payment_entry_for_employee(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	"""Function to make Payment Entry for Employee Advance, Gratuity, Expense Claim, Leave Encashment"""
	doc = frappe.get_doc(dt, dn)

	party_account = get_party_account(doc)
	party_account_currency = get_account_currency(party_account)
	payment_type = "Pay"
	grand_total, outstanding_amount = get_grand_total_and_outstanding_amount(
		doc, party_amount, party_account_currency
	)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = get_paid_amount_and_received_amount(
		doc, party_account_currency, bank, outstanding_amount, payment_type, bank_amount
	)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = "Employee"
	pe.party = doc.get("employee")
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.letter_head = doc.get("letter_head")
	pe.paid_from = bank.account
	pe.paid_to = party_account
	pe.paid_from_account_currency = bank.account_currency
	pe.paid_to_account_currency = party_account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.project = doc.get('custom_project')
	pe.akad = doc.get('custom_akad')
	pe.cost_center = doc.get('custom_cost_center')

	pe.append(
		"references",
		{
			"reference_doctype": dt,
			"reference_name": dn,
			"bill_no": doc.get("bill_no"),
			"due_date": doc.get("due_date"),
			"total_amount": grand_total,
			"outstanding_amount": outstanding_amount,
			"allocated_amount": outstanding_amount,
		},
	)

	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.set_missing_ref_details()

	if party_account and bank:
		reference_doc = None
		if dt == "Employee Advance":
			reference_doc = doc
		pe.set_exchange_rate(ref_doc=reference_doc)
		pe.set_amounts()

	return pe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_accounts_for_payment(doctype, txt, searchfield, start, page_len, filters):
    """
    Custom query for Payment Entry paid_from field
    Returns accounts matching either account_type OR root_type criteria
    """
    account_types = filters.get("account_types", [])
    root_types = filters.get("root_types", [])
    company = filters.get("company")
    
    # Ensure lists are properly formatted
    if isinstance(account_types, str):
        account_types = [account_types]
    if isinstance(root_types, str):
        root_types = [root_types]
    
    conditions = []
    values = []
    
    # Build the OR condition for account_type and root_type
    or_conditions = []
    
    if account_types:
        account_type_placeholders = ", ".join(["%s"] * len(account_types))
        or_conditions.append(f"account_type IN ({account_type_placeholders})")
        values.extend(account_types)
    
    if root_types:
        root_type_placeholders = ", ".join(["%s"] * len(root_types))
        or_conditions.append(f"root_type IN ({root_type_placeholders})")
        values.extend(root_types)
    
    # Combine OR conditions
    if or_conditions:
        conditions.append(f"({' OR '.join(or_conditions)})")
    
    # Add other mandatory conditions
    conditions.append("is_group = %s")
    values.append(0)
    
    conditions.append("company = %s")
    values.append(company)
    
    conditions.append("disabled = %s")
    values.append(0)
    
    # Add search condition if text is provided
    if txt:
        conditions.append("(name LIKE %s OR account_name LIKE %s)")
        values.extend([f"%{txt}%", f"%{txt}%"])
    
    # Build final query
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            name, 
            account_name, 
            account_type, 
            root_type,
            CONCAT_WS(' - ', name, account_name) as label
        FROM `tabAccount`
        WHERE {where_clause}
        ORDER BY 
            CASE WHEN name LIKE %s THEN 0 ELSE 1 END,
            idx DESC,
            name
        LIMIT %s OFFSET %s
    """
    
    # Add ordering and pagination parameters
    values.extend([f"{txt}%" if txt else "%", page_len, start])
    
    return frappe.db.sql(query, values, as_dict=False)