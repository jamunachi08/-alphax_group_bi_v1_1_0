frappe.query_reports["AGB Financial Matrix"] = {
    filters: [
        {fieldname: "template", label: __("Template"), fieldtype: "Link", options: "AGB Template", reqd: 1},
        {fieldname: "report_scope", label: __("Report Scope"), fieldtype: "Select", options: ["Single Company", "Multiple Companies", "Company Group"], default: "Single Company"},
        {fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company"},
        {
            fieldname: "companies",
            label: __("Companies"),
            fieldtype: "MultiSelectList",
            get_data: function(txt) { return frappe.db.get_link_options("Company", txt); }
        },
        {fieldname: "company_group", label: __("Company Group"), fieldtype: "Link", options: "AGB Company Group"},
        {fieldname: "time_mode", label: __("Time Mode"), fieldtype: "Select", options: ["Fiscal Year", "Date Range"], default: "Fiscal Year"},
        {fieldname: "fiscal_year", label: __("Fiscal Year"), fieldtype: "Link", options: "Fiscal Year", depends_on: "eval:doc.time_mode==='Fiscal Year'"},
        {fieldname: "from_date", label: __("From Date"), fieldtype: "Date", depends_on: "eval:doc.time_mode==='Date Range'"},
        {fieldname: "to_date", label: __("To Date"), fieldtype: "Date", depends_on: "eval:doc.time_mode==='Date Range'"},
        {fieldname: "periodicity", label: __("Periodicity"), fieldtype: "Select", options: ["Monthly", "Quarterly", "Yearly", "Total"], default: "Monthly"},
        {fieldname: "show_by", label: __("Show By"), fieldtype: "Select", options: ["Period", "Dimension"], default: "Period"},
        {
            fieldname: "dimension_fieldname",
            label: __("Dimension Field"),
            fieldtype: "Select",
            options: ["cost_center", "project", "finance_book", "company", "branch", "department"],
            default: "cost_center",
            depends_on: "eval:doc.show_by==='Dimension'"
        },
        {
            fieldname: "cost_centers",
            label: __("Cost Centers"),
            fieldtype: "MultiSelectList",
            get_data: function(txt) { return frappe.db.get_link_options("Cost Center", txt); }
        },
        {
            fieldname: "projects",
            label: __("Projects"),
            fieldtype: "MultiSelectList",
            get_data: function(txt) { return frappe.db.get_link_options("Project", txt); }
        },
        {
            fieldname: "finance_books",
            label: __("Finance Books"),
            fieldtype: "MultiSelectList",
            get_data: function(txt) { return frappe.db.get_link_options("Finance Book", txt); }
        },
        {
            fieldname: "custom_dimension_values",
            label: __("Custom Dimension Values"),
            fieldtype: "Data",
            depends_on: "eval:doc.show_by==='Dimension'",
            description: __("Optional comma-separated values for custom dimensions such as branch or department.")
        },
        {fieldname: "presentation_currency", label: __("Presentation Currency"), fieldtype: "Link", options: "Currency"}
    ],
    onload(report) {
        report.page.add_inner_message(__("Tip: use account tokens imported from the MAP workbook to link one label to many accounts."));
    }
}
