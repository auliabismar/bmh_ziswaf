# Copyright (c) 2025, PT Karya Tata Bangsa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class Donation(Document):
	def on_submit(self):
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.posting_date = self.donation_date
		journal_entry.voucher_type = self.doctype
		journal_entry.user_remark = self.note
		if self.bank_reference_no:
			journal_entry.cheque_no = self.bank_reference_no
			journal_entry.cheque_date = self.donation_date
		journal_entry.company = self.company
		debit_accounts = {}
		for account in self.accounts:
			key = (account.akad, self.account)
			if key not in debit_accounts:
				debit_accounts[key] = 0
			debit_accounts[key] += account.amount
		for key in debit_accounts:
			journal_entry.append('accounts', {
				'account': self.cashbank_account,
				'debit_in_account_currency': debit_accounts[key],
				'cost_center': self.cost_center,
				'akad': key,
			})
		for account in self.accounts:
			journal_entry.append(
				'accounts',
				{
					'account': account.account,
					'credit_in_account_currency': account.amount,
					'party_type': 'Donor',
					'party': self.donor,
					'cost_center': self.cost_center,
					'akad': account.akad,
					'project': account.project,	
					'user_remark': account.note,
				},
			)
		journal_entry.save()
		journal_entry.submit()
		self.db_set('journal_entry', journal_entry.name)

	def on_cancel(self):
		if self.journal_entry:
			journal_entry = frappe.get_doc('Journal Entry', self.journal_entry)
			journal_entry.cancel()
