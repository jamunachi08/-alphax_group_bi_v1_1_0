frappe.ui.form.on("AGB Template", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Load Example MAP"), () => {
                frm.call("load_example_map").then(() => frm.reload_doc());
            }, __("Actions"));

            frm.add_custom_button(__("Import MAP from First Attachment"), () => {
                frm.call("import_map_from_first_attachment").then(() => frm.reload_doc());
            }, __("Actions"));

            frm.add_custom_button(__("Build Default Columns"), () => {
                frm.call("build_default_columns").then(() => frm.reload_doc());
            }, __("Actions"));

            frm.add_custom_button(__("Clear Rows"), () => {
                frm.call("clear_rows").then(() => frm.reload_doc());
            }, __("Actions"));

            frm.add_custom_button(__("Preview Matrix"), () => {
                frappe.set_route("query-report", "AGB Financial Matrix", { template: frm.doc.name });
            }, __("Actions"));

            frm.dashboard.add_comment(__("Tip: map each line by Account, Account Group, or account tokens imported from your Excel MAP sheet."));
        }
    }
});
