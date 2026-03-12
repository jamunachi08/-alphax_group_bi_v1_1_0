from frappe.model.document import Document

class AGBCompanyGroup(Document):
    def validate(self):
        seen = set()
        cleaned = []
        for row in self.companies or []:
            if row.company and row.company not in seen:
                seen.add(row.company)
                cleaned.append(row)
        self.companies = cleaned
