import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "docs/pilot/mock/synthetic_reference_erp_v1";
const outputDir = "outputs/sprint5-mock-pilot";
await fs.mkdir(outputDir, { recursive: true });

const wb = Workbook.create();
const navy = "#17365D";
const blue = "#D9EAF7";
const amber = "#FFF2CC";
const red = "#F4CCCC";
const green = "#D9EAD3";

function title(sheet, text, columns) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${columns}1`).merge();
  sheet.getRange("A1").values = [[text]];
  sheet.getRange(`A1:${columns}1`).format = {
    fill: navy,
    font: { bold: true, color: "#FFFFFF", size: 15 },
    rowHeight: 28,
  };
}

function table(sheet, range, name) {
  const item = sheet.tables.add(range, true, name);
  item.style = "TableStyleMedium2";
  item.showFilterButton = true;
  return item;
}

const summary = wb.worksheets.add("Package");
title(summary, "Synthetic Reference ERP v1 — Mock Pilot Package", "F");
summary.getRange("A3:B13").values = [
  ["Property", "Value"],
  ["Classification", "GENERATED TEST DATA — NON-PRODUCTION"],
  ["Vendor", "Example Education Systems"],
  ["Product", "Synthetic Reference ERP"],
  ["Version", "1.0"],
  ["Transport", "In-process read-only CSV test double"],
  ["Network egress", "Disabled"],
  ["Credential", "None"],
  ["Real connector authority", "No"],
  ["Demo approval", "USER APPROVED 2026-08-05"],
  ["Replacement unit", "Replace entire synthetic_reference_erp_v1 folder"],
];
table(summary, "A3:B13", "PackageSummary");
summary.getRange("D3:E9").values = [
  ["Control", "Status"],
  ["Generated data only", "PASS"],
  ["No personal names/contact data", "PASS"],
  ["No network/credential", "PASS"],
  ["Mock thresholds clearly marked", "PASS"],
  ["Demo approval", "APPROVED"],
  ["Production approval", "BLOCKED"],
];
table(summary, "D3:E9", "PackageControls");
summary.getRange("E4:E8").format.fill = green;
summary.getRange("E9").format.fill = red;
summary.getRange("A14:F16").merge();
summary.getRange("A14").values = [["This package validates design and tests only. It must not be used for a real ERP, identity matching, credential authorization, privacy acceptance, or production thresholds."]];
summary.getRange("A14:F16").format = { fill: amber, wrapText: true, font: { bold: true } };

const inventory = wb.worksheets.add("Source Inventory");
title(inventory, "Generated Source Inventory", "I");
inventory.getRange("A3:I9").values = [
  ["Object", "Source key", "Incremental field", "Canonical entities", "Rows", "Required", "Retention class", "Schema version", "Owner"],
  ["academic_periods", "period_id", "updated_at", "academic-period", 1, "Yes", "structure", "1", "MOCK"],
  ["programmes", "programme_id", "updated_at", "programme; programme-version", 1, "Yes", "structure", "1", "MOCK"],
  ["courses", "course_id", "updated_at", "course; course-version", 1, "Yes", "structure", "1", "MOCK"],
  ["offerings", "offering_id", "updated_at", "offering", 1, "Yes", "structure", "1", "MOCK"],
  ["learners", "learner_id", "updated_at", "learner", 2, "Yes", "learner-minimised", "1", "MOCK"],
  ["enrolments", "enrolment_id", "updated_at", "programme-enrolment; offering-enrolment", 2, "Yes", "enrolment", "1", "MOCK"],
];
table(inventory, "A3:I9", "SourceInventory");

const mappings = wb.worksheets.add("Field Mappings");
title(mappings, "Generated Field-to-Canonical Mappings", "H");
const mappingRows = [
  ["Source object", "Source field", "Canonical entity", "Canonical field", "Transform", "Required", "Prohibited", "Notes"],
  ["academic_periods", "period_id", "academic-period", "source_record_key", "identity", "Yes", "No", "Stable generated key"],
  ["academic_periods", "code", "academic-period", "code", "copy", "Yes", "No", ""],
  ["academic_periods", "name", "academic-period", "name", "copy", "Yes", "No", ""],
  ["academic_periods", "period_type", "academic-period", "period_type", "enum-map", "Yes", "No", "academic_year|term"],
  ["academic_periods", "starts_on", "academic-period", "starts_on", "iso-date", "Yes", "No", ""],
  ["academic_periods", "ends_on", "academic-period", "ends_on", "iso-date", "Yes", "No", ""],
  ["academic_periods", "updated_at", "ingestion-metadata", "source_updated_at", "iso-datetime", "Yes", "No", "Observation metadata; not a canonical business field"],
  ["programmes", "programme_id", "programme", "source_record_key", "identity", "Yes", "No", "Stable generated key"],
  ["programmes", "code", "programme", "code", "copy", "Yes", "No", ""],
  ["programmes", "version_code", "programme-version", "version_code", "copy", "Yes", "No", ""],
  ["programmes", "name", "programme-version", "name", "copy", "Yes", "No", ""],
  ["programmes", "effective_from", "programme-version", "effective_from", "iso-date", "Yes", "No", ""],
  ["programmes", "updated_at", "ingestion-metadata", "source_updated_at", "iso-datetime", "Yes", "No", "Observation metadata; not a canonical business field"],
  ["courses", "course_id", "course", "source_record_key", "identity", "Yes", "No", "Stable generated key"],
  ["courses", "code", "course", "code", "copy", "Yes", "No", ""],
  ["courses", "version_code", "course-version", "version_code", "copy", "Yes", "No", ""],
  ["courses", "title", "course-version", "title", "copy", "Yes", "No", ""],
  ["courses", "credit_value", "course-version", "credit_value", "decimal", "Yes", "No", "0..100"],
  ["courses", "effective_from", "course-version", "effective_from", "iso-date", "Yes", "No", ""],
  ["courses", "updated_at", "ingestion-metadata", "source_updated_at", "iso-datetime", "Yes", "No", "Observation metadata; not a canonical business field"],
  ["offerings", "offering_id", "offering", "source_record_key", "identity", "Yes", "No", "Stable generated key"],
  ["offerings", "code", "offering", "code", "copy", "Yes", "No", ""],
  ["offerings", "period_id", "offering", "academic_period_source_key", "reference", "Yes", "No", ""],
  ["offerings", "course_id", "offering", "course_source_key", "reference", "Yes", "No", ""],
  ["offerings", "updated_at", "ingestion-metadata", "source_updated_at", "iso-datetime", "Yes", "No", "Observation metadata; not a canonical business field"],
  ["learners", "learner_id", "learner", "source_record_key", "identity", "Yes", "No", "Never displayed raw"],
  ["learners", "institution_reference", "learner", "institution_reference", "copy", "Yes", "No", "Generated only"],
  ["learners", "updated_at", "ingestion-metadata", "source_updated_at", "iso-datetime", "Yes", "No", "Observation metadata; not a canonical business field"],
  ["enrolments", "enrolment_id", "programme-enrolment", "source_record_key", "identity", "Yes", "No", "Stable generated key"],
  ["enrolments", "enrolment_id", "offering-enrolment", "source_record_key", "identity", "Yes", "No", "Stable generated key"],
  ["enrolments", "learner_id", "programme-enrolment", "learner_source_key", "reference", "Yes", "No", ""],
  ["enrolments", "programme_id", "programme-enrolment", "programme_source_key", "reference", "Yes", "No", ""],
  ["enrolments", "offering_id", "offering-enrolment", "offering_source_key", "reference", "Yes", "No", ""],
  ["enrolments", "effective_from", "programme-enrolment", "effective_from", "iso-date", "Yes", "No", ""],
  ["enrolments", "effective_from", "offering-enrolment", "effective_from", "iso-date", "Yes", "No", "Shared source effective date"],
  ["enrolments", "status", "programme-enrolment", "status", "enum-map", "Yes", "No", "active|completed|withdrawn"],
  ["enrolments", "status", "offering-enrolment", "status", "enum-map", "Yes", "No", "active|completed|withdrawn"],
  ["enrolments", "updated_at", "ingestion-metadata", "source_updated_at", "iso-datetime", "Yes", "No", "Observation metadata; not a canonical business field"],
];
mappings.getRange(`A3:H${mappingRows.length + 2}`).values = mappingRows;
table(mappings, `A3:H${mappingRows.length + 2}`, "FieldMappings");

const authority = wb.worksheets.add("Authority Matrix");
title(authority, "Mock Source Authority Matrix", "F");
authority.getRange("A3:F12").values = [
  ["Canonical entity", "Authority", "Effective from", "Correction", "Late arrival", "Approval"],
  ["academic-period", "primary", "2030-01-01", "source version", "reconcile", "MOCK"],
  ["programme", "primary", "2030-01-01", "source version", "reconcile", "MOCK"],
  ["programme-version", "primary", "2030-01-01", "source version", "reconcile", "MOCK"],
  ["course", "primary", "2030-01-01", "source version", "reconcile", "MOCK"],
  ["course-version", "primary", "2030-01-01", "source version", "reconcile", "MOCK"],
  ["offering", "primary", "2030-01-01", "source version", "reconcile", "MOCK"],
  ["learner", "primary", "2030-01-01", "source version", "no auto-merge", "MOCK"],
  ["programme-enrolment", "primary", "2030-01-01", "source version", "reconcile", "MOCK"],
  ["offering-enrolment", "primary", "2030-01-01", "source version", "reconcile", "MOCK"],
];
table(authority, "A3:F12", "AuthorityMatrix");

const identity = wb.worksheets.add("Identity Rules");
title(identity, "Mock Identity Resolution Rules", "E");
identity.getRange("A3:E9").values = [
  ["Priority", "Entity", "Rule", "Ambiguous result", "Automatic merge"],
  [1, "learner", "tenant + source system + learner_id exact", "reconciliation-required", "No"],
  [2, "academic-period", "tenant + source system + period_id exact", "reject", "No"],
  [3, "programme", "tenant + source system + programme_id exact", "reject", "No"],
  [4, "course", "tenant + source system + course_id exact", "reject", "No"],
  [5, "offering", "tenant + source system + offering_id exact", "reject", "No"],
  [6, "enrolment", "tenant + source system + enrolment_id exact", "reconciliation-required", "No"],
];
table(identity, "A3:E9", "IdentityRules");

const thresholds = wb.worksheets.add("Thresholds");
title(thresholds, "Mock Acceptance Thresholds — Never Production Authority", "F");
thresholds.getRange("A3:F9").values = [
  ["Metric", "Operator", "Value", "Unit", "Breach action", "Authority"],
  ["Completeness", ">=", 100, "percent", "block promotion", "MOCK"],
  ["Freshness", "<=", 60, "minutes", "block promotion", "MOCK"],
  ["Rejection rate", "<=", 5, "percent", "block promotion", "MOCK"],
  ["Duplicate rate", "<=", 2, "percent", "block promotion", "MOCK"],
  ["Unresolved reconciliation", "<=", 0, "count", "block promotion", "MOCK"],
  ["Unexplained count variance", "<=", 0, "count", "block promotion", "MOCK"],
];
table(thresholds, "A3:F9", "MockThresholds");
thresholds.getRange("A11:F13").merge();
thresholds.getRange("A11").values = [["These deterministic values test gate behavior only. A real source owner must replace and approve every threshold."]];
thresholds.getRange("A11:F13").format = { fill: amber, wrapText: true, font: { bold: true } };

const approvals = wb.worksheets.add("Approvals");
title(approvals, "Mock Package Approval Register", "E");
approvals.getRange("A3:E8").values = [
  ["Role", "Name", "Status", "Date", "Replacement requirement"],
  ["Demo sponsor", "User", "APPROVED", "2026-08-05", "Demo use only; never production"],
  ["Product owner", "MOCK", "NOT APPROVED", null, "Named accountable owner"],
  ["ERP/source owner", "MOCK", "NOT APPROVED", null, "Source inventory and thresholds"],
  ["Privacy owner", "MOCK", "NOT APPROVED", null, "Lawful purpose and lifecycle"],
  ["Security owner", "MOCK", "NOT APPROVED", null, "Credential, network and TLS policy"],
];
table(approvals, "A3:E8", "ApprovalRegister");
approvals.getRange("C4").format.fill = green;
approvals.getRange("C5:C8").format.fill = red;

for (const sheet of wb.worksheets.items) {
  const used = sheet.getUsedRange();
  used.format.font = { name: "Aptos", size: 10 };
  used.format.wrapText = true;
  used.format.autofitColumns();
  used.format.autofitRows();
  sheet.getRange("A:A").format.columnWidth = 22;
  sheet.freezePanes.freezeRows(3);
}
summary.getRange("B:B").format.columnWidth = 45;
mappings.getRange("A:B").format.columnWidth = 23;
mappings.getRange("C:D").format.columnWidth = 25;
mappings.getRange("E:G").format.columnWidth = 15;
mappings.getRange("H:H").format.columnWidth = 30;
mappings.getRange("H:H").format.columnWidth = 48;
inventory.getRange("A:D").format.columnWidth = 24;
inventory.getRange("E:I").format.columnWidth = 16;
identity.getRange("A:A").format.columnWidth = 10;
identity.getRange("B:B").format.columnWidth = 22;
identity.getRange("C:C").format.columnWidth = 42;
identity.getRange("D:E").format.columnWidth = 24;
thresholds.getRange("A:A").format.columnWidth = 28;
thresholds.getRange("B:D").format.columnWidth = 14;
thresholds.getRange("E:E").format.columnWidth = 22;

const inspect = await wb.inspect({ kind: "table", range: "Package!A1:F16", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 8 });
console.log(inspect.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "formula error scan" });
console.log(errors.ndjson);

for (const sheet of wb.worksheets.items) {
  const preview = await wb.render({ sheetName: sheet.name, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(`${outputDir}/${sheet.name.replaceAll(" ", "_")}.png`, new Uint8Array(await preview.arrayBuffer()));
}

const file = await SpreadsheetFile.exportXlsx(wb);
await file.save(`${outputDir}/pilot_matrices.xlsx`);
await file.save(`${root}/pilot_matrices.xlsx`);
