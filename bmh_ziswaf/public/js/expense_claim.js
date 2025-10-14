frappe.ui.form.on('Expense Claim', {
	refresh(frm) {
		frm.set_query('cost_center', () => {
      return {
        filters: {
          is_group: 0,
          company: frm.doc.company
        }
      }
    });
	},
});