GRC Cyber Security Assessment Tool
A modular Streamlit application for performing cyber security assessments across multiple companies, generating executive and detailed reports, managing recommendations, and exporting results to JSON, PDF, Word, and Roadmap CSV.
This tool is designed for:
cyber security assessments
internal audits
ISO / NIS2 / NIST / CIS aligned reviews
executive reporting
remediation tracking
Features
Core assessment capabilities
Multi-company support
Multiple assessments per company
Domain-based cyber security questionnaire
Weighted scoring model
Support for:
Fail
Partial
Pass
NotApplicable
Notes / observations per question
Proof image upload per question
Saved answers stored in SQLite
UI / workflow
Modular Streamlit architecture
Assessment navigation by domain
Previous / Next domain navigation
Domain-level helper actions:
Set all NotApplicable
Clear domain
Optional filtering by:
Applies To
Scope
Show only domains with saved answers
Executive Dashboard
Overall score
Domain scores
Maturity level
Progress bars with colors
Heatmap by domain
Trend across assessments for the same company
Evidence completeness metrics:
answers with notes
answers with proof
answers with notes + proof
Executive Summary
Manual executive summary
AI-generated executive summary
Recommendations auto-generated from saved answers
Recommendation table with:
risk
responsible owner
deadline
status
source (auto/manual)
Edit / Add / Delete recommendations
Duplicate prevention can be extended using `recommendation_key`
Export
JSON export
PDF export
Word export
Roadmap CSV export
Executive export mode
Detailed export mode
Optional inclusion of:
Proof Image
Control Mapping
Management-style export
Executive export supports:
introductory management text
Top 5 Priority Actions
Key Areas of Improvement
max bullets per domain (3 / 4 / 5)
manual edit before export
Control mapping
Supports displaying and exporting mappings such as:
ISO 27001
NIST CSF
CIS Controls
NIS2
Technology Stack
Python 3.11+ or 3.12+
Streamlit
SQLite
Pandas
Matplotlib
ReportLab
python-docx
OpenAI Python SDK (optional, for AI summary)
---
Project Structure
```bash
app.py
db.py
utils.py
auth.py
ai.py
json_io.py
word_report.py
requirements.txt
assessment_questions.json

uploads/
  <assessment_id>/
    questionid_filename.png

ui/
  __init__.py
  company.py
  assessment.py
  domains.py
  dashboard.py
  executive.py
  import_export.py
```
Main Modules
`app.py`
Application entry point.
Responsible for:
loading JSON assessment model
authentication
company / assessment context
tabs:
Assessment
Executive Dashboard
Executive Summary
Import / Export
`db.py`
SQLite database layer.
Responsible for:
schema initialization
users
companies
assessments
answers
executive summary
recommendations
`utils.py`
Shared helper functions.
Responsible for:
scoring
filtering
maturity calculation
charts
heatmap
trend
export helpers
management export content
PDF generation
`auth.py`
Authentication helper.
Responsible for:
login
session handling
role checks
`ai.py`
Optional AI integration for executive summary generation.
`json_io.py`
JSON import/export helpers.
`word_report.py`
Word document generation.
`ui/company.py`
Company and assessment selection UI.
`ui/assessment.py`
Assessment workflow orchestration.
`ui/domains.py`
Question rendering and answer saving.
`ui/dashboard.py`
Dashboard visuals and trend analysis.
`ui/executive.py`
Executive summary and recommendation management.
`ui/import_export.py`
All export/import logic and management export editor.
Installation
1. Clone or copy project
Place all files in one project folder, for example:
```bash
GRC/
```
2. Create virtual environment
Windows
```bash
python-m venv .venv
.venv\Scripts\activate
```
Linux / macOS
```bash
python3-m venv .venv
source .venv/bin/activate
```
3. Install dependencies
```bash
pip install-r requirements.txt
```
4. Run the application
```bash
streamlit run app.py
```
---
Requirements
Example `requirements.txt`:
```bash
streamlit==1.39.0
pandas==2.2.3
matplotlib==3.9.2
numpy==2.1.2
reportlab==4.2.2
python-docx==1.1.2
openai==1.51.2
```
---
First Login
Default user created automatically on first run:
Username: `admin`
Password: `admin`
You can create additional users from the sidebar if logged in as admin.
Roles
Supported roles:
`admin`
`auditor`
`viewer`
Admin
Can:
create users
create companies
create assessments
edit answers
edit recommendations
export / import
Auditor
Can:
create assessments
edit answers
edit recommendations
export / import
Viewer
Can:
view data
view dashboard
view reports
---
Database
The application uses SQLite:
```bash
assessment.db
```
Important
If you change schema significantly during development, it is often easiest to delete the DB once:
Windows
```bash
del assessment.db
```
Linux / macOS
```bash
rm assessment.db
```
Then restart the app so the schema is recreated.
---
Assessment JSON Model
The application expects a JSON file such as:
```json
{
  "meta": {
    "version":"2025-2026-v8",
    "scoring": {
      "Fail":0,
      "Partial":50,
      "Pass":100,
      "NotApplicable":null
    },
    "default_weight":1
  },
  "domains": [
    {
      "id":"asset_management",
      "name": {
        "ro":"Managementul activelor",
        "en":"Asset Management"
      },
      "questions": [
        {
          "id":"am_01",
          "text": {
            "ro":"Aveti un inventar complet al tuturor echipamentelor IT?",
            "en":"Do you have a complete inventory of all IT equipment?"
          },
          "answer_type":"score",
          "weight":5,
          "risk":"High",
          "recommendation": {
            "ro":"Implementati solutie automatizata de descoperire",
            "en":"Implement automated discovery solution"
          },
          "applies_to": ["IT"],
          "scope": ["Corporate"],
          "iso27001": ["A.5.9"],
          "nist_csf": ["ID.AM-01"]
        }
      ]
    }
  ]
}
```
---
Supported Question Fields
The app can use the following fields per question:
`id`
`text`
`answer_type`
`weight`
`risk`
`business_impact`
`remediation_priority`
`effort`
`default_owner_role`
`applies_to`
`scope`
`control_family`
`recommendation_key`
`recommendation`
`evidence_examples`
`expected_artifacts`
`iso27001`
`nist_csf`
`cis_control`
`nis2`
Optional advanced fields:
`supported_response_modes`
`options`
`scoring_logic`
Supported Answer Types
1. `score`
Uses the default scoring labels:
Fail
Partial
Pass
NotApplicable
2. `single_choice`
Uses:
`options`
`scoring_logic`
Example:
```json
{
  "answer_type":"single_choice",
  "options": {
    "ro": ["Manual","Mixt","Automat"],
    "en": ["Manual","Hybrid","Automated"]
  },
  "scoring_logic": {
    "Manual":0,
    "Hybrid":50,
    "Automated":100
  }
}
```
---
Workflow
1. Login
Log in as admin, auditor, or viewer.
2. Select company
Choose an existing company or create a new one.
3. Select assessment
Choose an existing assessment or create a new one.
4. Complete assessment
For each domain:
answer questions
add notes
upload proof image
save response
5. Review dashboard
Check:
overall score
domain scores
maturity
heatmap
evidence completeness
trend across assessments
6. Prepare executive summary
write manually
or generate via AI
7. Generate recommendations
auto-generate from saved Fail / Partial answers
review and edit
add manual recommendations if needed
8. Export
Choose:
Executive mode
Detailed mode
And choose whether to include:
Proof Image
Control Mapping
---
Assessment Tab Features
Inside a domain, you can:
answer each question
save each answer
upload proof image
add notes
see evidence examples and expected artifacts
see mapping to standards
You also have:
`Set all NotApplicable`
`Clear domain`
---
Executive Dashboard
The Executive Dashboard contains:
Overall score
Calculated from weighted domain scores.
Maturity
Current maturity level:
Initial
Repeatable
Defined
Managed
Optimized
Domain scores
Displayed using:
progress bars
score table
bar chart
heatmap
Trend pe Evaluari
Shows score evolution over time for the same company.
Example:
Q1 assessment = 42
Q2 assessment = 58
Q3 assessment = 71
Useful for:
management reporting
audit comparisons
remediation tracking
Evidence completeness
Tracks how complete assessment evidence is:
answers with notes
answers with proof
answers with both notes and proof
---
Recommendations
Recommendations are stored in one unified table.
Each recommendation has:
domain
source (`auto` / `manual`)
recommendation text
risk
responsible
deadline
status
Auto-generated recommendations
Generated from saved answers with:
score `0` (Fail)
score `50` (Partial)
Manual recommendations
Can be added from the UI.
Recommendation status board
You can extend the UI to show:
Critical Open
High Open
Done Total
---
Export Modes
Executive
Designed for management / board / leadership.
Includes:
company
assessment
overall score
domain scores
executive summary
intro management text
Top 5 Priority Actions
Key Areas of Improvement by domain
Can be edited before export.
Does not need:
detailed notes
full mappings
proof image paths
answer-by-answer tables
Detailed
Designed for technical / audit / remediation work.
Includes:
all executive sections
recommendation tables
assessment details
notes
optional proof image path
optional control mapping
---
Management Export Editor
For Executive export, the UI provides an editable editor for:
Intro text
Examples:
English
`The recommendations below should be prioritized in order of importance.`
Romanian
`Recomandarile de mai jos trebuie prioritizate in ordinea importantei.`
Top 5 Priority Actions
One line = one action.
Key Areas of Improvement
Per domain:
one line = one bullet
configurable maximum bullets per domain:
3
4
5
This lets you refine the export before generating the final PDF / Word.
---
Exports
JSON
Contains structured assessment data:
metadata
scores
summary
answers
recommendations
mapping rows
export options
PDF
Suitable for:
sharing
static reporting
executive presentations
Word
Suitable for:
editing
client delivery
consulting output
Roadmap CSV
Sorted by:
risk
owner
deadline
Useful for:
PMO
remediation planning
tracking in Excel / Power BI
Control Mapping
If enabled, exports can include mappings for:
ISO 27001
NIST CSF
CIS Controls
NIS2
This is useful for:
audit traceability
standard alignment
compliance reporting
---
Proof Image Handling
Proof image is stored as a file path in the application database.
The current export behavior includes or excludes the proof path, depending on the selected export option.
If you want real image embedding into Word/PDF later, that can be implemented separately.
---
Troubleshooting
1. `ImportError: cannot import name ...`
Cause:
outdated file version
mismatch between imports and file contents
Fix:
replace the whole target file with the latest version
ensure all imports exist in `utils.py`
2. `NameError: name 'ui' is not defined`
Cause:
`ui/__init__.py` contains invalid text
Fix:
`ui/__init__.py` should be empty or contain only:
```bash
# ui package
```
3. Dashboard shows 0 even after saving answers
Cause:
dashboard using session state instead of DB
or answers were not actually saved
Fix:
ensure `get_answers_for_assessment()` is used
verify header shows `Saved answers: X/Y`
4. PDF table text overlaps
Cause:
raw text in ReportLab table cells
Fix:
use `Paragraph` objects
wrap text
keep narrow font and proper padding
5. `st.session_state` widget mutation error
Cause:
assigning to widget state after widget is instantiated in the same run
Fix:
use separate staging keys
update then rerun
6. Old DB schema problems
Fix:
Delete the old DB:
```bash
rm assessment.db
```
or on Windows:
```bash
del assessment.db
```
---
Development Notes
Suggested future improvements
Save all answers in domain
Set all Pass / Partial / Fail per domain
Real duplicate prevention by `recommendation_key`
Better status board widget
Embedded proof images in Word/PDF
Versioning of exported reports
Audit trail / history
Reminder system for overdue recommendations
Owner-based roadmap export
Graphical summary pages in PDF
White-label branding
Multi-tenant deployment
---
Security Notes
This is a local assessment tool and stores:
users
assessments
notes
proof paths
recommendations
Recommended production improvements:
password hashing with stronger scheme (bcrypt / argon2)
encrypted file storage
role enforcement across all write paths
secure backups
audit logging
per-user authorization checks
HTTPS and reverse proxy if deployed
---
Deployment Notes
For local use:
```bash
streamlit run app.py
```
For internal deployment, you can run behind:
Nginx
Docker
Streamlit Community Cloud
internal VM / server
Recommended production stack:
Docker
persistent volume for DB + uploads
reverse proxy
environment variables for secrets
---
Example Use Cases
NIS2 readiness assessment
ISO 27001 gap assessment
OT / ICS cyber review
Azure / M365 security review
DevSecOps maturity review
internal audit preparation
board-level cyber summary
remediation planning workshop
---
