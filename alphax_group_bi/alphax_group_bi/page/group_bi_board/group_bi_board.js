frappe.pages["group-bi-board"].on_page_load = function(wrapper) {
    frappe.ui.make_app_page({parent: wrapper, title: __("Group BI Board"), single_column: true});

    $(wrapper).html(`
        <div class="agb-help-box">
            <strong>${__("What this page is for")}</strong><br>
            ${__("Use this page for a quick matrix preview. For deeper analysis, open the AGB Financial Matrix report.")}
        </div>
        <div class="agb-board-card">
            <div class="row">
                <div class="col-md-4" id="template-field"></div>
                <div class="col-md-4" id="company-field"></div>
                <div class="col-md-4" id="fiscal-year-field"></div>
            </div>
            <div class="row mt-3">
                <div class="col-md-3" id="show-by-field"></div>
                <div class="col-md-3" id="dimension-field"></div>
                <div class="col-md-3" id="currency-field"></div>
                <div class="col-md-3 d-flex align-items-end">
                    <button class="btn btn-primary w-100" id="agb-run-board">${__("Run Board")}</button>
                </div>
            </div>
        </div>
        <div class="agb-board-card"><div id="agb-chart"></div></div>
        <div class="agb-board-card"><div id="agb-table"></div></div>
    `);

    const mk = (parent, df) => frappe.ui.form.make_control({parent: $(parent), df: df, render_input: true});
    const fields = {
        template: mk("#template-field", {fieldtype: "Link", label: __("Template"), fieldname: "template", options: "AGB Template", reqd: 1}),
        company: mk("#company-field", {fieldtype: "Link", label: __("Company"), fieldname: "company", options: "Company"}),
        fiscal_year: mk("#fiscal-year-field", {fieldtype: "Link", label: __("Fiscal Year"), fieldname: "fiscal_year", options: "Fiscal Year"}),
        show_by: mk("#show-by-field", {fieldtype: "Select", label: __("Show By"), fieldname: "show_by", options: ["Period", "Dimension"], default: "Period"}),
        dimension_fieldname: mk("#dimension-field", {fieldtype: "Select", label: __("Dimension Field"), fieldname: "dimension_fieldname", options: ["cost_center", "project", "finance_book", "branch", "department"], default: "cost_center"}),
        presentation_currency: mk("#currency-field", {fieldtype: "Link", label: __("Presentation Currency"), fieldname: "presentation_currency", options: "Currency"}),
    };

    const render_table = payload => {
        const head = payload.columns.map(c => `<th>${frappe.utils.escape_html(c.label)}</th>`).join("");
        const body = payload.data.map(row => "<tr>" + payload.columns.map(c => `<td>${row[c.fieldname] == null ? "" : frappe.format(row[c.fieldname], c)}</td>`).join("") + "</tr>").join("");
        $("#agb-table").html(`<div class="table-responsive"><table class="table table-bordered table-sm"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`);
    };

    $("#agb-run-board").on("click", () => {
        const filters = {
            template: fields.template.get_value(),
            company: fields.company.get_value(),
            fiscal_year: fields.fiscal_year.get_value(),
            show_by: fields.show_by.get_value(),
            dimension_fieldname: fields.dimension_fieldname.get_value(),
            presentation_currency: fields.presentation_currency.get_value(),
            report_scope: "Single Company",
            time_mode: "Fiscal Year",
            periodicity: "Monthly"
        };
        frappe.call({
            method: "alphax_group_bi.alphax_group_bi.api.report_engine.run_report",
            args: {filters},
            callback: function(r) {
                const payload = r.message || {};
                render_table(payload);
                $("#agb-chart").empty();
                if (payload.chart && payload.chart.data && frappe.Chart) {
                    new frappe.Chart("#agb-chart", payload.chart);
                } else {
                    $("#agb-chart").html(`<div class="text-muted">${__("No chart data returned.")}</div>`);
                }
            }
        });
    });
};
