# Copyright (c) 2025, PT Karya Tata Bangsa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class Donation(Document):
	def on_submit(self):
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.posting_date = self.donation_date
		#journal_entry.voucher_type = self.doctype
		journal_entry.user_remark = self.remark
		if self.bank_reference_no:
			journal_entry.cheque_no = self.bank_reference_no
			journal_entry.cheque_date = self.donation_date
		journal_entry.company = self.company
		receiving_akad = frappe.get_single_value('ZISWaf Setting', 'receiving_akad')
		akad = frappe.get_all('ZISWaf Akad Setting', fields=['akad', 'percentage', 'against_account'])
		accounts = []
		for account in self.accounts:
			matches = [item for item in akad if item['akad'] == account.akad]
			if matches and account.akad != receiving_akad:
				amount = account.amount * matches[0].percentage / 100
				accounts.append({
					'account': account.account,
					'amount': amount,
					'akad': account.akad,
					'cost_center': self.cost_center,
					'project': account.project,
					'note': account.note,
				})
				accounts.append({
					'account': matches[0].against_account,
					'amount': account.amount - amount,
					'akad': receiving_akad,
					'cost_center': self.cost_center,
					'note': account.note,
				})
			else:
				accounts.append({
					'account': account.account,
					'amount': account.amount,
					'akad': account.akad,
					'cost_center': self.cost_center,
					'project': account.project,
					'note': account.note,
				})
		debit_accounts = {}
		for account in accounts:
			key = (account.get('akad'), self.cashbank_account)
			if key not in debit_accounts:
				debit_accounts[key] = 0
			debit_accounts[key] += account.get('amount')
		for key in debit_accounts:
			journal_entry.append('accounts', {
				'account': self.cashbank_account,
				'debit_in_account_currency': debit_accounts[key],
				'cost_center': self.cost_center,
				'akad': key,
			})
		for account in accounts:
			journal_entry.append(
				'accounts',
				{
					'account': account.get('account'),
					'credit_in_account_currency': account.get('amount'),
					'party_type': 'Donor' if account.get('account') != receiving_akad else None,
					'party': self.donor if account.get('account') != receiving_akad else None,
					'cost_center': account.get('cost_center'),
					'akad': account.get('akad'),
					'project': account.get('project'),
					'user_remark': account.get('note'),
				},
			)
		journal_entry.save()
		journal_entry.submit()
		self.db_set('journal_entry', journal_entry.name)

	def on_cancel(self):
		if self.journal_entry:
			journal_entry = frappe.get_doc('Journal Entry', self.journal_entry)
			journal_entry.cancel()
