// In your custom app's public/js/payment_entry.js
// Override paid_from filter with custom query

frappe.ui.form.on("Payment Entry", {
  setup: function (frm) {
    // Override the paid_from query
    frm.set_query("paid_from", function () {
      frm.events.validate_company(frm);

      var account_types = ["Pay", "Internal Transfer"].includes(frm.doc.payment_type)
        ? ["Bank", "Cash"]
        : [frappe.boot.party_account_types[frm.doc.party_type]];

      if (frm.doc.party_type == "Shareholder") {
        account_types.push("Equity");
      }

      // For Supplier/Customer, use custom query with OR condition
      if (["Supplier", "Customer"].includes(frm.doc.party_type)) {
        return {
          query: "bmh_ziswaf.overrides.erpnext.get_accounts_for_payment",
          filters: {
            account_types: account_types,
            root_types: ["Expense", "Liability", "Income"],
            company: frm.doc.company
          }
        };
      } else {
        // Default behavior for other party types
        return {
          filters: {
            account_type: ["in", account_types],
            is_group: 0,
            company: frm.doc.company
          }
        };
      }
    });
  }
});