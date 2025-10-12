# Copyright (c) 2025, PT Karya Tata Bangsa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class Donation(Document):
	def on_submit(self):
		journal_entry_name = self._create_journal_entry()
		self.db_set('journal_entry', journal_entry_name)

	def on_cancel(self):
		if self.journal_entry:
			frappe.get_doc('Journal Entry', self.journal_entry).cancel()

	def _create_journal_entry(self):
		journal_entry = frappe.new_doc('Journal Entry')
		journal_entry.posting_date = self.donation_date
		journal_entry.user_remark = self.remark
		journal_entry.company = self.company
		if self.bank_reference_no:
			journal_entry.cheque_no = self.bank_reference_no
			journal_entry.cheque_date = self.donation_date
		akad_settings = get_akad_settings()
		self._create_ziswaf_receive_rows(journal_entry)
		self._create_amil_allocation_rows(journal_entry, akad_settings)
		journal_entry.save()
		journal_entry.submit()
		return journal_entry.name

	def _create_ziswaf_receive_rows(self, journal_entry):
		for account in self.accounts:
			journal_entry.append('accounts', {
				'account': account.account,
				'credit_in_account_currency': account.amount,
				'party_type': 'Donor',
				'party': self.donor,
				'cost_center': account.cost_center,
				'akad': account.akad,
				'project': account.project,
			})
			journal_entry.append('accounts', {
				'account': self.cashbank_account,
				'debit_in_account_currency': account.amount,
				'cost_center': account.cost_center,
				'akad': account.akad,
				'project': account.project,
			})

	def _create_amil_allocation_rows(self, journal_entry, settings):
		akad_setting = settings['akad_settings']
		for account in self.accounts:
			key =  account.akad
			if key == 'Infak':
				if account.account in settings['infak_terikat']:
					key = f'{account.akad}-Terikat'
				elif account.account in settings['infak_tidak_terikat']:
					key = f'{account.akad}-Tidak Terikat'
			setting = akad_setting.get(key)
			if not setting:
				frappe.throw(_('Akad Setting for {0} is not found. Please contact Administrator.').format(key))
			journal_entry.append('accounts', {
				'account': setting['amil_allocation_account'],
				'debit_in_account_currency': account.amount * setting['percentage'] / 100,
				'cost_center': account.cost_center,
				'akad': account.akad,
				'project': account.project,
			})
			journal_entry.append('accounts', {
				'account': self.cashbank_account,
				'credit_in_account_currency': account.amount * setting['percentage'] / 100,
				'cost_center': account.cost_center,
				'akad': account.akad,
				'project': account.project,
			})
			journal_entry.append('accounts', {
				'account': self.cashbank_account,
				'debit_in_account_currency': account.amount * setting['percentage'] / 100,
				'cost_center': account.cost_center,
				'akad': settings['receiving_akad'],
			})
			journal_entry.append('accounts', {
				'account': setting['against_account'],
				'credit_in_account_currency': account.amount * setting['percentage'] / 100,
				'cost_center': account.cost_center,
				'akad': settings['receiving_akad'],
			})
			
def get_akad_settings():
	receiving_akad = frappe.get_single_value('ZISWaf Setting', 'receiving_akad')
	if not receiving_akad:
		frappe.throw('Receiving Akad in ZISWaf Setting is not found. Please contact Administrator.')
	akad_list = frappe.get_all('ZISWaf Akad Setting', 
		fields=['akad', 'percentage', 'against_account', 'amil_allocation_account', 'infak_type'])
	infak_terikat = frappe.get_all('ZISWaf Setting Account', 
		filters={'parentfield': 'infak_terikat'}, pluck='account')
	infak_tidak_terikat = frappe.get_all('ZISWaf Setting Account', 
		filters={'parentfield': 'infak_tidak_terikat'}, pluck='account')
	csr = frappe.get_all('ZISWaf Setting Account', 
		filters={'parentfield': 'csr'}, pluck='account')
	if not akad_list:
		frappe.throw('ZISWaf Akad Setting is not found. Please contact Administrator.')
	akad_settings = {}
	for item in akad_list:
		key = item['akad'] if not item.get('infak_type') else f"{item['akad']}-{item['infak_type']}"
		akad_settings[key] = {k: v for k, v in item.items() if k != 'infak_type'}
	return {
		'receiving_akad': receiving_akad,
		'akad_settings': akad_settings,
		'infak_terikat': infak_terikat,
		'infak_tidak_terikat': infak_tidak_terikat,
		'csr': csr
	}