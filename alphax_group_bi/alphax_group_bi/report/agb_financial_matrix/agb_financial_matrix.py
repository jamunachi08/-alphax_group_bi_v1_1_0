from alphax_group_bi.alphax_group_bi.api.report_engine import build_report

def execute(filters=None):
    payload = build_report(filters or {})
    return payload.get("columns", []), payload.get("data", []), payload.get("message"), payload.get("chart")
