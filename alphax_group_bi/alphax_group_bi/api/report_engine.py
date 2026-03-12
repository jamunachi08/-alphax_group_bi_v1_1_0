from __future__ import annotations

import ast
import calendar
import re
from datetime import date
from functools import lru_cache
from typing import Dict, List, Tuple

import frappe
from frappe import _
from frappe.utils import flt, getdate


def get_company_currency(company: str | None) -> str | None:
    if not company:
        return None
    return frappe.db.get_value("Company", company, "default_currency")


def get_group_companies(group_name: str | None) -> List[str]:
    if not group_name:
        return []
    return frappe.get_all("AGB Company Group Company", filters={"parent": group_name}, pluck="company")


def resolve_companies(filters: Dict) -> List[str]:
    companies = []

    for key in ("company",):
        if filters.get(key):
            companies.append(filters.get(key))

    raw_companies = filters.get("companies")
    if raw_companies:
        if isinstance(raw_companies, str):
            companies.extend([c.strip() for c in raw_companies.split(",") if c.strip()])
        elif isinstance(raw_companies, (list, tuple)):
            companies.extend([c for c in raw_companies if c])

    if filters.get("company_group"):
        companies.extend(get_group_companies(filters.get("company_group")))

    seen = []
    for company in companies:
        if company and company not in seen:
            seen.append(company)
    return seen


def get_periods(filters: Dict) -> List[Tuple[str, date, date]]:
    time_mode = filters.get("time_mode") or "Fiscal Year"
    periodicity = filters.get("periodicity") or "Monthly"

    if time_mode == "Fiscal Year":
        fy = filters.get("fiscal_year")
        if not fy:
            frappe.throw(_("Fiscal Year is required when Time Mode is Fiscal Year."))
        fy_start, fy_end = frappe.db.get_value("Fiscal Year", fy, ["year_start_date", "year_end_date"])
        start = getdate(fy_start)
        end = getdate(fy_end)
    else:
        start = getdate(filters.get("from_date"))
        end = getdate(filters.get("to_date"))
        if not start or not end:
            frappe.throw(_("From Date and To Date are required when Time Mode is Date Range."))

    if start > end:
        frappe.throw(_("From date cannot be later than To date."))

    if periodicity == "Total":
        return [("Total", start, end)]

    periods = []
    if periodicity == "Monthly":
        cursor = date(start.year, start.month, 1)
        while cursor <= end:
            last_day = calendar.monthrange(cursor.year, cursor.month)[1]
            pend = date(cursor.year, cursor.month, last_day)
            periods.append((cursor.strftime("%b %Y"), max(start, cursor), min(end, pend)))
            cursor = date(cursor.year + 1, 1, 1) if cursor.month == 12 else date(cursor.year, cursor.month + 1, 1)
        return [p for p in periods if p[1] <= p[2]]

    if periodicity == "Quarterly":
        cursor = date(start.year, ((start.month - 1) // 3) * 3 + 1, 1)
        while cursor <= end:
            quarter = ((cursor.month - 1) // 3) + 1
            end_month = quarter * 3
            last_day = calendar.monthrange(cursor.year, end_month)[1]
            pend = date(cursor.year, end_month, last_day)
            periods.append((f"Q{quarter} {cursor.year}", max(start, cursor), min(end, pend)))
            cursor = date(cursor.year + 1, 1, 1) if end_month == 12 else date(cursor.year, end_month + 1, 1)
        return [p for p in periods if p[1] <= p[2]]

    if periodicity == "Yearly":
        cursor = date(start.year, 1, 1)
        while cursor <= end:
            pend = date(cursor.year, 12, 31)
            periods.append((str(cursor.year), max(start, cursor), min(end, pend)))
            cursor = date(cursor.year + 1, 1, 1)
        return [p for p in periods if p[1] <= p[2]]

    frappe.throw(_("Unsupported periodicity: {0}").format(periodicity))


def get_dimension_filters(filters: Dict) -> Dict[str, tuple]:
    out = {}
    for source_key, gle_key in (
        ("cost_centers", "cost_center"),
        ("projects", "project"),
        ("finance_books", "finance_book"),
    ):
        vals = filters.get(source_key)
        if not vals:
            continue
        if isinstance(vals, str):
            parsed = tuple(v.strip() for v in vals.split(",") if v.strip())
        else:
            parsed = tuple(v for v in vals if v)
        if parsed:
            out[gle_key] = parsed
    return out


def get_dimension_field(filters: Dict) -> str | None:
    if (filters.get("show_by") or "Period") != "Dimension":
        return None
    return filters.get("dimension_fieldname") or "cost_center"


SAFE_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b if b else 0,
}

SAFE_UNARY_OPS = {
    ast.USub: lambda a: -a,
    ast.UAdd: lambda a: a,
}


def safe_eval_formula(expr: str, context: Dict[str, float]) -> float:
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return flt(context.get(node.id, 0))
        if isinstance(node, ast.BinOp) and type(node.op) in SAFE_BIN_OPS:
            return SAFE_BIN_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_UNARY_OPS:
            return SAFE_UNARY_OPS[type(node.op)](_eval(node.operand))
        raise ValueError("Unsafe formula")
    return flt(_eval(ast.parse(expr, mode="eval")))


def _norm(value):
    value = (value or "").strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


@lru_cache(maxsize=1)
def _account_lookup():
    rows = frappe.get_all(
        "Account",
        fields=["name", "account_name", "account_number", "company"],
        limit_page_length=0,
    )
    exact_name = {}
    norm_map = {}
    for row in rows:
        for key in filter(None, [
            row.name,
            row.account_name,
            row.account_number,
            f"{row.account_number} - {row.account_name}" if row.account_number and row.account_name else None,
            f"{row.account_number} - {row.account_name} - {row.company}" if row.account_number and row.account_name and row.company else None,
        ]):
            exact_name.setdefault(key, row.name)
            norm_map.setdefault(_norm(key), row.name)
    return exact_name, norm_map


def resolve_account_tokens(account_tokens: str | None) -> List[str]:
    if not account_tokens:
        return []
    tokens = []
    for part in re.split(r"[\n,;]+", account_tokens):
        token = part.strip()
        if token:
            tokens.append(token)

    exact_name, norm_map = _account_lookup()
    resolved = []
    seen = set()
    for token in tokens:
        match = exact_name.get(token) or norm_map.get(_norm(token))
        if match and match not in seen:
            seen.add(match)
            resolved.append(match)
    return resolved


def get_row_accounts(row) -> List[str]:
    if row.account:
        return [row.account]

    if row.account_group:
        if cint(row.include_children):
            lft, rgt = frappe.db.get_value("Account", row.account_group, ["lft", "rgt"])
            return frappe.get_all("Account", filters={"lft": (">=", lft), "rgt": ("<=", rgt)}, pluck="name")
        return [row.account_group]

    return resolve_account_tokens(row.account_tokens)


def root_type_for_row(row, accounts: List[str]) -> str | None:
    if row.account:
        return frappe.db.get_value("Account", row.account, "root_type")
    if row.account_group:
        return frappe.db.get_value("Account", row.account_group, "root_type")
    if accounts:
        return frappe.db.get_value("Account", accounts[0], "root_type")
    return None


def cint(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def get_row_amount(filters: Dict, row, start_date: date, end_date: date, companies: List[str], dimension_field: str | None = None, dimension_value: str | None = None) -> float:
    if row.row_type in ("Heading", "Spacer", "Formula", "Total"):
        return 0.0

    accounts = get_row_accounts(row)
    if not accounts:
        return 0.0

    conditions = ["posting_date between %(start)s and %(end)s", "is_cancelled = 0", "account in %(accounts)s"]
    params = {"start": start_date, "end": end_date, "accounts": tuple(accounts)}

    if companies:
        conditions.append("company in %(companies)s")
        params["companies"] = tuple(companies)

    if row.company_override:
        conditions.append("company = %(row_company)s")
        params["row_company"] = row.company_override

    for gle_key, values in get_dimension_filters(filters).items():
        conditions.append(f"`tabGL Entry`.`{gle_key}` in %({gle_key})s")
        params[gle_key] = values

    if dimension_field and dimension_value and frappe.get_meta("GL Entry").has_field(dimension_field):
        conditions.append(f"`tabGL Entry`.`{dimension_field}` = %(dimension_value)s")
        params["dimension_value"] = dimension_value

    sql = f"""
        select
            sum(credit - debit) as income_style,
            sum(debit - credit) as expense_style
        from `tabGL Entry`
        where {' and '.join(conditions)}
    """
    result = frappe.db.sql(sql, params, as_dict=True)[0] or {}
    root_type = root_type_for_row(row, accounts)
    amount = flt(result.get("income_style") if root_type == "Income" else result.get("expense_style"))
    return amount * flt(row.sign_factor or 1)


def bucket_dimension_values(filters: Dict) -> List[str]:
    custom_values = filters.get("custom_dimension_values")
    if custom_values:
        if isinstance(custom_values, str):
            vals = [v.strip() for v in custom_values.split(",") if v.strip()]
        else:
            vals = [v for v in custom_values if v]
        return vals

    dimension_field = get_dimension_field(filters)
    doctype_map = {
        "cost_center": "Cost Center",
        "project": "Project",
        "finance_book": "Finance Book",
        "company": "Company",
        "department": "Department",
        "branch": "Branch",
    }
    if dimension_field in doctype_map and frappe.db.exists("DocType", doctype_map[dimension_field]):
        return frappe.get_all(doctype_map[dimension_field], pluck="name", limit=20)
    return ["(Unspecified)"]


def build_report(filters: Dict) -> Dict:
    template_name = filters.get("template")
    if not template_name:
        frappe.throw(_("Template is required."))

    template = frappe.get_doc("AGB Template", template_name)
    companies = resolve_companies(filters)
    report_currency = filters.get("presentation_currency")
    if not report_currency:
        report_currency = (
            get_company_currency(filters.get("company"))
            or get_company_currency(template.default_company)
            or (frappe.db.get_value("AGB Company Group", filters.get("company_group"), "reporting_currency") if filters.get("company_group") else None)
            or (get_company_currency(companies[0]) if companies else None)
        )

    show_by = filters.get("show_by") or "Period"
    dimension_field = get_dimension_field(filters)

    if show_by == "Period":
        buckets = get_periods(filters)
        labels = [b[0] for b in buckets]
    else:
        dimension_values = bucket_dimension_values(filters) or ["(Unspecified)"]
        buckets = [(v, None, None) for v in dimension_values]
        labels = [b[0] for b in buckets]

    columns = [{"label": _("Row"), "fieldname": "row_label", "fieldtype": "Data", "width": 320}]
    for label in labels:
        columns.append({"label": label, "fieldname": frappe.scrub(label), "fieldtype": "Currency", "width": 140, "options": report_currency})
    columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 140, "options": report_currency})

    data = []
    chart_labels = []
    chart_values = []
    computed_by_bucket = {label: {} for label in labels}

    ordered_rows = sorted(template.row_mappings, key=lambda d: (d.sequence or 0, d.idx or 0))

    for row in ordered_rows:
        row_key = row.row_key or frappe.scrub(row.row_label)
        out = {"row_label": row.row_label}
        total = 0.0

        if row.row_type in ("Formula", "Total") and row.formula:
            for label in labels:
                amount = safe_eval_formula(row.formula, computed_by_bucket[label])
                computed_by_bucket[label][row_key] = amount
                out[frappe.scrub(label)] = amount
                total += flt(amount)
        elif row.row_type in ("Heading", "Spacer"):
            for label in labels:
                out[frappe.scrub(label)] = None
            computed_by_bucket[labels[0]][row_key] = 0 if labels else 0
        else:
            for label, start_date, end_date in buckets:
                if show_by == "Period":
                    amount = get_row_amount(filters, row, start_date, end_date, companies)
                else:
                    if filters.get("time_mode") == "Fiscal Year" and filters.get("fiscal_year"):
                        fy_start, fy_end = frappe.db.get_value("Fiscal Year", filters.get("fiscal_year"), ["year_start_date", "year_end_date"])
                        start_date, end_date = getdate(fy_start), getdate(fy_end)
                    else:
                        start_date, end_date = getdate(filters.get("from_date")), getdate(filters.get("to_date"))
                    amount = get_row_amount(filters, row, start_date, end_date, companies, dimension_field, label if label != "(Unspecified)" else None)
                computed_by_bucket[label][row_key] = amount
                out[frappe.scrub(label)] = amount
                total += flt(amount)

        out["total"] = total if row.row_type not in ("Heading", "Spacer") else None
        data.append(out)

        if row.row_type not in ("Heading", "Spacer"):
            chart_labels.append(row.row_label)
            chart_values.append(total)

    return {
        "columns": columns,
        "data": data,
        "message": _("Presentation Currency: {0}").format(report_currency or "-"),
        "chart": {
            "data": {
                "labels": chart_labels[:8],
                "datasets": [{"name": _("Total"), "values": chart_values[:8]}]
            },
            "type": "bar"
        }
    }


@frappe.whitelist()
def run_report(filters=None):
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)
    return build_report(filters or {})
