# Semester Result Analysis Dashboard

A desktop dashboard for analyzing semester/student results using Python, Pandas, NumPy and Matplotlib. Tkinter provides the GUI. CSV is the default data source; an optional MySQL repository is included for database-backed deployments.

## Features
- Load semester results from CSV and append student subject results from Excel workbooks (`.xlsx`).
- Clean missing/invalid marks and calculate total, percentage and grade.
- KPI cards: unique students, students passing every subject, class average, and pass rate.
- Class insights: top performers, highest/lowest subject averages, student grade counts, semester comparisons, attendance correlation, and students flagged for failing at least one subject or averaging below 50%.
- Dark sidebar with semester and section filters.
- Searchable student table with average percentage, average attendance, grade, pass/fail status, semester and section.
- Two charts display side by side and can be selected independently. They explain their units and scope: student grade counts, subject averages, student-level semester averages, 10-point result bands, and one attendance/result point per student.
- Export the filtered and searched student summary to CSV.
- Optional MySQL repository for larger deployments.
- Automated unit tests.

## Technology
Python 3.10+, NumPy, Pandas, Matplotlib, openpyxl, Tkinter. Optional: mysql-connector-python.

## Run
```bash
pip install -r requirements.txt
python main.py
```

If Tkinter is missing on Linux, install your OS Python Tk package (for example `python3-tk`).

## Test
```bash
pytest -q
```

## CSV schema
`student_id,name,semester,section,subject,marks,max_marks,attendance`

One row represents one student's subject result. `sample_results.csv` is included.
Excel imports (`.xlsx`) use the same column names on the first worksheet. Include `semester` and
`section` values on every row; after import, the dashboard selects those filters
automatically when the workbook contains exactly one semester and one section.

## MySQL (optional)
See `docs/DATABASE.md` for the schema and configuration. The application works without MySQL.
