frappe.ui.form.on('Employee Advance', {
	refresh(frm) {
		frm.events.get_akad(frm);
	},
	advance_account(frm) {
		frm.events.get_akad(frm);
	},
	custom_cost_center(frm) {
		frm.toggle_display('mode_of_payment', !!frm.doc.custom_cost_center);
		frm.set_query('mode_of_payment', () => {
			return {
				filters: {
					custom_cost_center: frm.doc.custom_cost_center,
					enabled: 1,
				}
			}
		});
	},
	get_akad(frm) {
		if (frm.doc.advance_account && frm.is_new()) {
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