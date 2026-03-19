import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

def calculate_scores(responses):
    domain_totals = {}
    domain_weights = {}

    for r in responses:
        score = r.get("score")
        if score is None:  # NotApplicable
            continue
        d = r["domain"]
        w = r.get("weight", 1)
        domain_totals[d] = domain_totals.get(d, 0) + score * w
        domain_weights[d] = domain_weights.get(d, 0) + w

    scores = {}
    for d in domain_totals:
        if domain_weights[d] > 0:
            scores[d] = round(domain_totals[d] / domain_weights[d])
        else:
            scores[d] = 0
    return scores


def get_maturity_level(score):
    if score >= 90: return "Optimized"
    if score >= 70: return "Managed"
    if score >= 45: return "Defined"
    if score >= 20: return "Repeatable"
    return "Initial"


def generate_chart(scores):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(scores.keys(), scores.values())
    ax.set_ylabel("Scor ponderat (0-100)")
    ax.set_title("Rezultate evaluare")
    ax.set_ylim(0, 100)
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_pdf(scores, recommendations):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("Raport Evaluare Securitate Cibernetica", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Scoruri pe domenii:", styles["Heading2"]))
    for domain, score in scores.items():
        elements.append(Paragraph(f"{domain}: {score:.0f} / 100", styles["Normal"]))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Recomandari:", styles["Heading2"]))
    elements.append(Paragraph(recommendations.replace("\n", "<br/>"), styles["Normal"]))

    # grafic
    chart_buf = generate_chart(scores)
    elements.append(Spacer(1, 20))
    elements.append(Image(chart_buf, width=480, height=240))

    doc.build(elements)
    buffer.seek(0)
    return buffer
