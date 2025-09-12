// Copyright (c) 2025, PT Karya Tata Bangsa and contributors
// For license information, please see license.txt

frappe.ui.form.on("Donation", {
	refresh(frm) {
		frm.trigger('calculate_total_donation');
	},
	validate(frm) {
		if (frm.doc.total_donation <= 0) {
			frappe.throw(__('Total Donation must be greater than 0'));
		}
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
	cost_center(frm) {
		if (frm.doc.accounts) {
			frm.doc.accounts.forEach(function (d) {
				d.cost_center = frm.doc.cost_center;
			});
		}
		frm.refresh_field('accounts');
	}
});

frappe.ui.form.on('Donation Account', {
	amount(frm, cdt, cdn) {
		frm.trigger('calculate_total_donation');
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
