from docx import Document
from docx.shared import Inches
from io import BytesIO

def generate_word(scores, recommendations, company_name, assessment_name):
    doc = Document()

    # Title
    doc.add_heading("Cyber Security Assessment Report", 0)

    doc.add_paragraph(f"Company: {company_name}")
    doc.add_paragraph(f"Assessment: {assessment_name}")

    doc.add_heading("Executive Summary", 1)

    avg_score = sum(scores.values()) / len(scores) if scores else 0

    doc.add_paragraph(f"Overall Security Score: {round(avg_score,2)}")

    # Domain scores
    doc.add_heading("Domain Scores", 1)

    for d, s in scores.items():
        doc.add_paragraph(f"{d}: {round(s,2)}")

    # Recommendations
    doc.add_heading("Recommendations", 1)

    for r in recommendations.split("\n"):
        if r.strip():
            doc.add_paragraph(r, style="List Bullet")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer
