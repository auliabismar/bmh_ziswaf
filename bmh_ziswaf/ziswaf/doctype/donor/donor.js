// Copyright (c) 2025, PT Karya Tata Bangsa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Donor', {
	refresh(frm) {
    if(!frm,is_new()){
      frappe.contacts.render_address_and_contact(frm);
    } else {
      frappe.contacts.clear_address_and_contact(frm);
    }
	},
});
