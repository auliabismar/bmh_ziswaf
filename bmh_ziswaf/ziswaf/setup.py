from frappe.desk.page.setup_wizard.setup_wizard import make_records

def make_custom_records():
  records = [
    {'doctype': 'Party Type', 'party_type': 'Donor', 'account_type': 'Receivable'},
  ]
  make_records(records)

def setup_ziswaf():
  make_custom_records()

data = {
	'on_setup': 'non_profit.setup.setup_non_profit'
}