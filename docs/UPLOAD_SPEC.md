Upload specification — Equipment CSV/PDF

Purpose
Provide a simple, robust default format and rules for admins to bulk-upload equipment into the Sport Equipment System. This avoids mixed-up entries and ensures imports map cleanly to the database model.

Supported upload formats
- CSV (preferred)
- PDF containing a clear table with header row matching the CSV columns

Required columns (CSV header)
- name (string) — Equipment name, e.g. "Ball"
- category (string) — Category name, e.g. "Football"
- category_code (string) — Unique short code (alphanumeric) used for fast search/filtering, e.g. "FTB01"; stored uppercase
- quantity (integer) — Number of units to add (0 or positive)

CSV rules and tips
1. Use UTF-8 encoding.
2. Include a header row with the exact column names above (case-insensitive).
3. Provide one equipment item per row.
4. Ensure `category_code` is unique across rows and existing DB entries; the importer will increment quantity for existing `category_code` matches.
5. Avoid commas inside fields unless you quote fields with double quotes.
6. If quantity is empty or not an integer, it's treated as 0.

Example (samples/equipment_template.csv)
name,category,category_code,quantity
Footballs,Football,FTB01,10
Goal nets,Football,FTB02,5

PDF rules
- PDFs must contain a textual table (not scanned images); the importer uses `pdfplumber` to extract the first table found.
- The table header should map to the CSV columns. If no table is found, the importer attempts to parse page text as CSV-like lines.
- For scanned PDFs, OCR is required — contact the admin to use Tesseract + pytesseract support (not enabled by default).

Common causes of 'mixed up' imports and how to avoid
- Missing header row: the importer cannot map columns and will produce wrong fields. Always include the header row.
- Using a free-form bullet list (one-per-line without columns): The importer treats each line as a single field. Use the sample CSV or the "Bulk Paste" UI (if enabled) instead.
- Duplicate category_code values: importer will treat the row as an update (increment quantity). If you intended separate items, give unique codes.

Recommended admin UX (default workflow)
1. Download `samples/equipment_template.csv` as a template.
2. Edit the file in Excel/Sheets or a text editor, keep UTF-8 encoding.
3. Upload using Admin → Receive New Equipment → Bulk Upload (choose CSV).
4. After upload, check flash messages for summary and any row warnings.

Optional alternatives to reduce errors
- Provide a "Bulk Paste" textarea in the UI where admins paste newline-separated names and optionally a prefix for auto-generated category codes (FTB -> FTB01, FTB02...). This reduces typing and avoids header/format errors.
- Implement a dry-run mode to preview changes before committing.
- Provide a downloadable error report if rows failed to import.

Implementation notes
- The importer expects `category_code` to be unique and uppercases it. It increments quantity if a matching code exists; otherwise it creates a new equipment row.
- PDF parsing uses `pdfplumber` (add `pdfplumber` to requirements). For scanned PDFs, OCR with `pytesseract` + Tesseract is required and must be installed on the server.

If you'd like, I can:
- Add a "Download sample CSV" button on the upload form (quick), and/or
- Implement a Bulk Paste UI that auto-generates codes from a prefix (recommended for speed).
