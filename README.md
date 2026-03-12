# AlphaX Group BI

AlphaX Group BI is a Frappe / ERPNext app for matrix-style financial reporting driven by a mapping table.

## What this app does
- Build report templates where each row can map to:
  - one account
  - multiple accounts
  - an account group
  - a formula
- Import starter row mappings from an attached MAP workbook
- Run the **AGB Financial Matrix** script report with:
  - company / multiple companies / company group scope
  - date range or fiscal year
  - monthly / quarterly / yearly / total buckets
  - optional dimension view (cost center / project / finance book / branch / department)

## Included starter mapping
This package includes a starter sample map generated from the uploaded workbook:
`Consolidated Budget And  P&L - Template.xlsx`

Detected classifications: 21

## Install
```bash
bench get-app <repo-or-path>
bench --site yoursite install-app alphax_group_bi
bench --site yoursite migrate
bench --site yoursite clear-cache
bench build --app alphax_group_bi
```

## Quick start
1. Open **AGB Template**
2. Create a new template
3. Use **Load Example MAP** or attach your own workbook and use **Import MAP from First Attachment**
4. Save the template
5. Open **AGB Financial Matrix**
6. Select template and reporting filters, then run

## Notes
- The app reads from **GL Entry**.
- Formula rows use row keys, for example:
  `revenue - cost_of_sales`
- Account token matching tries exact name, account number, account name, and normalized forms.
- Review starter formulas before production use.

## Files
- sample map csv: `alphax_group_bi/sample_maps/example_map.csv`
- starter rows json: `alphax_group_bi/sample_maps/example_map.json`
