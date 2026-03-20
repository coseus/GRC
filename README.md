# GRC Cyber Security Assessment Tool

A modular Streamlit application for performing cyber security assessments across multiple companies, generating executive and detailed reports, managing recommendations, and exporting results to JSON, PDF, Word, and Roadmap CSV.

This tool is designed for:
- cyber security assessments
- internal audits
- ISO / NIS2 / NIST / CIS aligned reviews
- executive reporting
- remediation tracking

---

# Features

## Core assessment capabilities
- Multi-company support
- Multiple assessments per company
- Domain-based cyber security questionnaire
- Weighted scoring model
- Support for:
  - Fail
  - Partial
  - Pass
  - NotApplicable
- Notes / observations per question
- Proof image upload per question
- Saved answers stored in SQLite

## UI / workflow
- Modular Streamlit architecture
- Assessment navigation by domain
- Previous / Next domain navigation
- Domain-level helper actions:
  - Set all NotApplicable
  - Clear domain
- Optional filtering by:
  - Applies To
  - Scope
- Show only domains with saved answers

## Executive Dashboard
- Overall score
- Domain scores
- Maturity level
- Progress bars with colors
- Heatmap by domain
- Trend across assessments for the same company
- Evidence completeness metrics:
  - answers with notes
  - answers with proof
  - answers with notes + proof

## Executive Summary
- Manual executive summary
- AI-generated executive summary
- Recommendations auto-generated from saved answers
- Recommendation table with:
  - risk
  - responsible owner
  - deadline
  - status
  - source (auto/manual)
- Edit / Add / Delete recommendations
- Duplicate prevention can be extended using `recommendation_key`

## Export
- JSON export
- PDF export
- Word export
- Roadmap CSV export
- Executive export mode
- Detailed export mode
- Optional inclusion of:
  - Proof Image
  - Control Mapping

## Management-style export
Executive export supports:
- introductory management text
- Top 5 Priority Actions
- Key Areas of Improvement
- max bullets per domain (3 / 4 / 5)
- manual edit before export

## Control mapping
Supports displaying and exporting mappings such as:
- ISO 27001
- NIST CSF
- CIS Controls
- NIS2

---

# Technology Stack

- Python 3.11+ or 3.12+
- Streamlit
- SQLite
- Pandas
- Matplotlib
- ReportLab
- python-docx
- OpenAI Python SDK (optional, for AI summary)

---

# Project Structure

```text
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
