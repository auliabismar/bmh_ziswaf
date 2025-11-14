# your_app/overrides/custom_loan.py
import frappe
from frappe import _
from lending.loan_management.doctype.loan.loan import Loan as BaseLoan

class CustomLoan(BaseLoan):
	def validate_accounts(self):
		for fieldname in [
			"payment_account",
			"loan_account",
		]:
			company = frappe.get_value("Account", self.get(fieldname), "company")

			if company != self.company:
				frappe.throw(
					_("Account {0} does not belongs to company {1}").format(
						frappe.bold(self.get(fieldname)), frappe.bold(self.company)
					)
				)
