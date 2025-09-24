frappe.ui.form.on('Employee Advance', {
	refresh(frm) {
		frm.events.get_akad(frm);
	},
	advance_account(frm) {
		frm.events.get_akad(frm);
	},
	get_akad(frm) {
		if (frm.doc.advance_account) {
			frappe.db.get_doc('Account', frm.doc.advance_account).then(account_doc => {
				let akad_options = (account_doc.custom_akad || []).map(r => r.akad);
				frm.set_query('custom_akad', () => {
					return {
						filters: [['Akad', 'name', 'in', akad_options]]
					}
				});
				if (akad_options.length === 1) {
					frm.set_value('custom_akad', akad_options[0])
				}
			});
		}
	},
});