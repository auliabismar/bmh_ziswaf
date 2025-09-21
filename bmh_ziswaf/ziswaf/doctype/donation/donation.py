# Copyright (c) 2025, PT Karya Tata Bangsa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class Donation(Document):
	def on_submit(self):
		journal_entry = self._create_journal_entry()
		self._process_accounts(journal_entry)
		journal_entry.save()
		journal_entry.submit()
		self.db_set('journal_entry', journal_entry.name)

	def on_cancel(self):
		if self.journal_entry:
			journal_entry = frappe.get_doc('Journal Entry', self.journal_entry)
			journal_entry.cancel()

	def _create_journal_entry(self):
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.posting_date = self.donation_date
		journal_entry.user_remark = self.remark
		if self.bank_reference_no:
			journal_entry.cheque_no = self.bank_reference_no
			journal_entry.cheque_date = self.donation_date
		journal_entry.company = self.company
		return journal_entry

	def _process_accounts(self, journal_entry):
		receiving_akad, akad_settings = self._get_akad_settings()
		processed_accounts = self._get_processed_accounts(receiving_akad, akad_settings)
		self._append_debit_entries(journal_entry, processed_accounts)
		self._append_credit_entries(journal_entry, processed_accounts, receiving_akad)

	def _get_akad_settings(self):
		receiving_akad = frappe.get_single_value('ZISWaf Setting', 'receiving_akad')
		akad_list = frappe.get_all(
      'ZISWaf Akad Setting', fields=['akad', 'percentage', 'against_account']
    )
		akad_settings = {item['akad']: item for item in akad_list}
		return receiving_akad, akad_settings
	
	def _get_processed_accounts(self, receiving_akad, akad_settings):
		process_accounts = []
		for account in self.accounts:
			akad_setting = akad_settings.get(account.akad)
			if akad_setting and account.akad != receiving_akad:
				amount = account.amount * akad_setting.percentage / 100
				process_accounts.append({
					'account': account.account,
					'amount': amount,
					'akad': account.akad,
					'cost_center': self.cost_center,
					'project': account.project,
					'note': account.note,
				})
				process_accounts.append({
					'account': akad_setting.against_account,
					'amount': account.amount - amount,
					'akad': receiving_akad,
					'cost_center': self.cost_center,
					'note': account.note,
				})
			else:
				process_accounts.append({
					'account': account.account,
					'amount': account.amount,
					'akad': account.akad,
					'cost_center': self.cost_center,
					'project': account.project,
					'note': account.note,
				})
		return process_accounts
	
	def _append_debit_entries(self, journal_entry, processed_accounts):
		debit_account = {}
		for account in processed_accounts:
			key = (account.get('akad'), self.cashbank_account)
			debit_account.setdefault(key, 0)
			debit_account[key] += account.get('amount')
		for key, amount in debit_account.items():
			journal_entry.append('accounts', {
				'account': self.cashbank_account,
				'debit_in_account_currency': amount,
				'cost_center': self.cost_center,
				'akad': key[0]
			})

	def _append_credit_entries(self, journal_entry, processed_accounts, receiving_akad):
		for account in processed_accounts:
			is_donor_entry = account.get('account') != receiving_akad
			journal_entry.append(
				'accounts',
				{
					'account': account.get('account'),
					'credit_in_account_currency': account.get('amount'),
					'party_type': 'Donor' if is_donor_entry else None,
					'party': self.donor if is_donor_entry else None,
					'cost_center': account.get('cost_center'),
					'akad': account.get('akad'),
					'project': account.get('project'),
					'user_remark': account.get('note'),
				},
			)