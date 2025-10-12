// Copyright (c) 2025, PT Karya Tata Bangsa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Donation', {
	refresh(frm) {
		frm.trigger('calculate_total_donation');
	},
	validate(frm) {
		if (frm.doc.docstatus === 0) {
			if (frm.doc.total_donation <= 0) {
				frappe.throw(__('Total Donation must be greater than 0'));
			}
			frm.trigger('validate_unique_accounts');
		}
	},
	cost_center(frm) {
		if (frm.doc.accounts) {
			frm.doc.accounts.forEach(function (d) {
				d.cost_center = frm.doc.cost_center;
			});
		}
		frm.refresh_field('accounts');
	},
	calculate_total_donation(frm) {
		let total_donation = 0;
		if (frm.doc.accounts) {
			frm.doc.accounts.forEach(function (d) {
				total_donation += d.amount;
			});
		}
		frm.set_value('total_donation', total_donation);
	},
	validate_unique_accounts(frm) {
		let accounts = frm.doc.accounts || [];
		let combinations = {};
		let has_duplicate = false;
		accounts.forEach(function(row, idx) {
			if (!row.account || !row.cost_center || !row.akad) return;
			let key = `${row.account}|${row.cost_center}|${row.akad}|${row.project || ''}`;
			if (combinations[key]) {
				has_duplicate = true;
				frappe.msgprint({
					title: __('Duplicate Entry'),
					indicator: 'red',
					message: __('Row {0}: Duplicate combination of Account, Cost Center, Akad and Project found in Row {1}',
						[idx + 1, combinations[key]])
				})
				frappe.validated = false;
			} else {
				combinations[key] = idx + 1;
			}
		})
		return !has_duplicate;
	}
});

frappe.ui.form.on('Donation Account', {
	amount(frm, cdt, cdn) {
		frm.trigger('calculate_total_donation');
	},
	account(frm, cdt, cdn) {
		let child = locals[cdt][cdn]
		if (!child.account) return;
		frappe.db.get_doc('Account', child.account).then(account_doc => {
			let akad_options = (account_doc.custom_akad || []).map(r => r.akad);
			frm.fields_dict['accounts'].grid.get_field('akad').get_query = function(doc, cdt, cdn) {
				return {
					filters: [['Akad', 'name', 'in', akad_options]]
				}
			}
			if (akad_options.length === 1) {
				frappe.model.set_value(cdt, cdn, 'akad', akad_options[0])
			}
			frm.refresh_field('accounts')
		});
		frm.trigger('validate_unique_accounts');
	},
	cost_center(frm, cdt, cdn) {
		frm.trigger('validate_unique_accounts');
	},
	akad(frm, cdt, cdn) {
		frm.trigger('validate_unique_accounts');
	},
	project(frm, cdt, cdn) {
		frm.trigger('validate_unique_accounts');
	},
	accounts_remove(frm, cdt, cdn) {
		frm.trigger('calculate_total_donation');
	},
	accounts_add(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		row.cost_center = frm.doc.cost_center;
		row.note = `Donor: ${frm.doc.donor}.`;
		frm.refresh_field('accounts');
	}
});
