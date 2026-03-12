import frappe
from frappe import _
from frappe.model.document import Document

from alphax_group_bi.utils.mapping import template_rows_from_sample, parse_map_file

def _safe_scrub(value: str) -> str:
    return frappe.scrub(value or "")

class AGBTemplate(Document):
    def validate(self):
        seen = set()
        for row in self.row_mappings or []:
            if not row.row_key:
                row.row_key = _safe_scrub(row.row_label or f"row_{row.idx}")
            if row.row_key in seen:
                frappe.throw(_("Duplicate row key: {0}").format(row.row_key))
            seen.add(row.row_key)

    @frappe.whitelist()
    def clear_rows(self):
        self.set("row_mappings", [])
        self.save()
        return True

    @frappe.whitelist()
    def load_example_map(self):
        self.set("row_mappings", [])
        for row in template_rows_from_sample():
            self.append("row_mappings", row)
        if not self.description:
            self.description = "Starter template loaded from the uploaded MAP workbook. Review formulas, row types, and account links before production use."
        self.save()
        frappe.msgprint(_("Example MAP loaded successfully."))
        return True

    @frappe.whitelist()
    def build_default_columns(self):
        self.set("column_schema", [])
        defaults = [
            {"column_label": "Current Period", "time_bucket": "Current Period", "periodicity": "Monthly"},
            {"column_label": "Prior Period", "time_bucket": "Prior Period", "periodicity": "Monthly", "period_offset": -1},
            {"column_label": "YTD", "time_bucket": "YTD", "periodicity": "Yearly"},
        ]
        for row in defaults:
            self.append("column_schema", row)
        self.save()
        frappe.msgprint(_("Default columns created."))
        return True

    @frappe.whitelist()
    def import_map_from_first_attachment(self):
        files = frappe.get_all(
            "File",
            filters={"attached_to_doctype": self.doctype, "attached_to_name": self.name},
            fields=["name"],
            order_by="creation asc"
        )
        if not files:
            frappe.throw(_("Attach a CSV or XLSX file to this template first."))

        file_doc = frappe.get_doc("File", files[0].name)
        parsed = parse_map_file(file_doc)

        grouped = {}
        for row in parsed:
            classification = (
                row.get("P&L Classification")
                or row.get("classification")
                or row.get("Classification")
                or row.get("col_3")
                or ""
            ).strip()
            account_token = (
                row.get("Chart of account")
                or row.get("chart of account")
                or row.get("Account")
                or row.get("col_2")
                or ""
            ).strip()

            if not classification:
                continue

            grouped.setdefault(classification, [])
            if account_token and account_token not in grouped[classification]:
                grouped[classification].append(account_token)

        self.set("row_mappings", [])
        for idx, (classification, tokens) in enumerate(grouped.items(), start=1):
            self.append("row_mappings", {
                "sequence": idx,
                "row_key": _safe_scrub(classification),
                "row_label": classification,
                "row_type": "Account",
                "classification": classification,
                "account_tokens": "\n".join(tokens),
                "sign_factor": 1,
            })

        self.save()
        frappe.msgprint(_("Rows imported from the first attachment."))
        return True
