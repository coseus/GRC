from io import BytesIO
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def localize(text_obj, lang: str):
    if isinstance(text_obj, dict):
        return text_obj.get(lang) or text_obj.get("en") or next(iter(text_obj.values()))
    return str(text_obj)


def build_question_index(data: dict):
    result = {}
    for domain in data["domains"]:
        for q in domain["questions"]:
            result[q["id"]] = {
                "domain_id": domain["id"],
                "domain_name": domain["name"],
                **q,
            }
    return result


def collect_filter_values(data: dict):
    applies_values = set()
    scope_values = set()

    for domain in data["domains"]:
        for q in domain["questions"]:
            for item in q.get("applies_to", []):
                applies_values.add(item)
            for item in q.get("scope", []):
                scope_values.add(item)

    return sorted(applies_values), sorted(scope_values)


def question_matches_filters(question: dict, selected_applies, selected_scope):
    q_applies = set(question.get("applies_to", []))
    q_scope = set(question.get("scope", []))

    applies_ok = True
    scope_ok = True

    if selected_applies:
        applies_ok = (not q_applies) or bool(q_applies.intersection(set(selected_applies)))

    if selected_scope:
        scope_ok = (not q_scope) or bool(q_scope.intersection(set(selected_scope)))

    return applies_ok and scope_ok


def filter_domains(data: dict, selected_applies, selected_scope):
    if not selected_applies and not selected_scope:
        return data["domains"]

    filtered_domains = []
    for domain in data["domains"]:
        kept_questions = [
            q for q in domain["questions"]
            if question_matches_filters(q, selected_applies, selected_scope)
        ]
        if kept_questions:
            filtered_domains.append({
                **domain,
                "questions": kept_questions,
            })
    return filtered_domains


def calculate_scores(responses):
    domain_totals = {}
    domain_weights = {}

    for r in responses:
        score = r.get("score")
        if score is None:
            continue
        domain = r["domain"]
        weight = r.get("weight", 1)
        domain_totals[domain] = domain_totals.get(domain, 0) + (score * weight)
        domain_weights[domain] = domain_weights.get(domain, 0) + weight

    results = {}
    for domain in domain_totals:
        w = domain_weights.get(domain, 0)
        results[domain] = round(domain_totals[domain] / w, 1) if w else 0
    return results


def calculate_overall_score(domain_scores):
    if not domain_scores:
        return 0.0
    return round(sum(domain_scores.values()) / len(domain_scores), 1)


def calculate_answered_stats(filtered_domains, score_map, session_state):
    total = 0
    answered = 0
    for domain in filtered_domains:
        for q in domain["questions"]:
            total += 1
            label = session_state.get(f"score_{q['id']}", "NotApplicable")
            if score_map.get(label) is not None:
                answered += 1
    return answered, total


def calculate_evidence_completeness(responses):
    scored = len(responses)
    if scored == 0:
        return {
            "scored_answers": 0,
            "with_notes": 0,
            "with_proof": 0,
            "with_notes_and_proof": 0,
            "notes_pct": 0.0,
            "proof_pct": 0.0,
            "complete_pct": 0.0,
        }

    with_notes = sum(1 for r in responses if str(r.get("notes", "")).strip())
    with_proof = sum(1 for r in responses if str(r.get("proof", "")).strip())
    with_notes_and_proof = sum(
        1 for r in responses
        if str(r.get("notes", "")).strip() and str(r.get("proof", "")).strip()
    )

    return {
        "scored_answers": scored,
        "with_notes": with_notes,
        "with_proof": with_proof,
        "with_notes_and_proof": with_notes_and_proof,
        "notes_pct": round(with_notes / scored * 100, 1),
        "proof_pct": round(with_proof / scored * 100, 1),
        "complete_pct": round(with_notes_and_proof / scored * 100, 1),
    }


def get_maturity_level(score):
    if score >= 90:
        return "Optimized"
    if score >= 75:
        return "Managed"
    if score >= 55:
        return "Defined"
    if score >= 30:
        return "Repeatable"
    return "Initial"


def score_to_hex(score):
    if score < 50:
        return "#d32f2f"
    if score < 75:
        return "#f9a825"
    return "#2e7d32"


def render_progress_bar_html(label, score, maturity):
    color = score_to_hex(score)
    width = max(2, min(100, int(score)))
    return f"""
    <div style="margin-bottom:14px;">
      <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
        <span style="font-weight:600;">{label}</span>
        <span>{score:.1f}/100 | {maturity}</span>
      </div>
      <div style="background:#e9ecef; border-radius:10px; width:100%; height:18px; overflow:hidden;">
        <div style="width:{width}%; background:{color}; height:18px; border-radius:10px;"></div>
      </div>
    </div>
    """


def generate_bar_chart(scores):
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = list(scores.keys())
    values = list(scores.values())
    color_list = [score_to_hex(v) for v in values]

    ax.barh(labels, values, color=color_list)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Score")
    ax.set_title("Domain Scores")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


def generate_heatmap(scores):
    domains = list(scores.keys())
    if not domains:
        domains = ["No data"]
        values = np.array([[0]])
    else:
        values = np.array([list(scores.values())])

    fig, ax = plt.subplots(figsize=(10, 2.8))
    cax = ax.imshow(values, cmap="RdYlGn", aspect="auto", vmin=0, vmax=100)

    ax.set_yticks([0])
    ax.set_yticklabels(["Score"])
    ax.set_xticks(range(len(domains)))
    ax.set_xticklabels(domains, rotation=35, ha="right")
    ax.set_title("Domain Heatmap")

    for i, v in enumerate(values[0]):
        ax.text(i, 0, f"{v:.0f}", va="center", ha="center", color="black", fontsize=10)

    fig.colorbar(cax, ax=ax, fraction=0.03, pad=0.04)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


def generate_trend_chart(df_trend: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x_labels = [f"{row['Assessment']}\n{row['Date'][:10]}" for _, row in df_trend.iterrows()]
    y_values = df_trend["Overall"].tolist()

    ax.plot(x_labels, y_values, marker="o", linewidth=2)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Overall score")
    ax.set_title("Assessment Trend")
    ax.grid(alpha=0.3)

    for x, y in zip(x_labels, y_values):
        ax.text(x, y + 2, f"{y:.0f}", ha="center", fontsize=9)

    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


def safe_score_label_from_value(score_value, score_map):
    inverse = {v: k for k, v in score_map.items()}
    return inverse.get(score_value, "NotApplicable")


def get_score_from_single_choice(question, selected_label):
    scoring_logic = question.get("scoring_logic", {})
    if selected_label in scoring_logic:
        return scoring_logic[selected_label]
    return None


def build_mapping_rows(responses, question_index, lang):
    rows = []
    for r in responses:
        qid = r.get("question_id")
        meta = question_index.get(qid, {})
        rows.append({
            "domain": r.get("domain", ""),
            "question": r.get("question", ""),
            "iso27001": ", ".join(meta.get("iso27001", [])),
            "nist_csf": ", ".join(meta.get("nist_csf", [])),
            "cis_control": ", ".join(meta.get("cis_control", [])),
            "nis2": ", ".join(meta.get("nis2", [])),
        })
    return rows


def sort_recommendations_by_risk(recommendations):
    risk_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
    return sorted(
        recommendations,
        key=lambda r: (
            risk_order.get(r.get("risk", ""), 99),
            r.get("domain_name", "") or "",
            r.get("text", "") or "",
        ),
    )


def sort_recommendations_for_roadmap(recommendations):
    risk_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
    return sorted(
        recommendations,
        key=lambda r: (
            risk_order.get(r.get("risk", ""), 99),
            (r.get("responsible", "") or "").lower(),
            r.get("deadline") if r.get("deadline") else "9999-12-31",
            r.get("domain_name", "") or "",
            r.get("text", "") or "",
        ),
    )


def get_management_intro(lang: str) -> str:
    if lang == "ro":
        return "Recomandarile de mai jos trebuie prioritizate in ordinea importantei."
    return "The recommendations below should be prioritized in order of importance."


def build_management_export_content(recommendations, lang="en", max_per_domain=3):
    recommendations = sort_recommendations_by_risk(recommendations)

    grouped = defaultdict(list)
    for r in recommendations:
        domain = r.get("domain_name", "Other")
        text = (r.get("text", "") or "").strip()
        if text:
            grouped[domain].append(r)

    domain_blocks = {}
    top_actions = []

    for domain, items in grouped.items():
        seen = set()
        kept = []
        for item in items:
            text = (item.get("text", "") or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            kept.append(text)
            if len(kept) >= max_per_domain:
                break
        domain_blocks[domain] = kept

    seen_top = set()
    for item in recommendations:
        text = (item.get("text", "") or "").strip()
        if not text or text in seen_top:
            continue
        seen_top.add(text)
        top_actions.append(text)
        if len(top_actions) >= 5:
            break

    return {
        "intro": get_management_intro(lang),
        "top_actions": top_actions,
        "domain_blocks": domain_blocks,
    }


def generate_pdf(
    company_name,
    assessment_name,
    assessment_date,
    overall_score,
    domain_scores,
    summary,
    recommendations,
    mapping_rows,
    responses=None,
    include_proof=False,
    include_mapping=False,
    export_mode="Executive",
    management_content=None,
):
    recommendations = sort_recommendations_by_risk(recommendations)
    responses = responses or []
    management_content = management_content or {
        "intro": "",
        "top_actions": [],
        "domain_blocks": {},
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading2"]

    table_cell = ParagraphStyle(
        "TableCell",
        parent=normal,
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        spaceAfter=0,
        spaceBefore=0,
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=normal,
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        leftIndent=14,
        firstLineIndent=-8,
        spaceAfter=4,
    )

    story = []

    story.append(Paragraph("Cyber Security Assessment Report", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Company: {company_name}", normal))
    story.append(Paragraph(f"Assessment: {assessment_name}", normal))
    story.append(Paragraph(f"Date: {assessment_date}", normal))
    story.append(Paragraph(f"Export mode: {export_mode}", normal))
    story.append(Paragraph(f"Overall Score: {overall_score:.1f}/100", normal))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Executive Summary", heading))
    story.append(Paragraph((summary or "-").replace("\n", "<br/>"), normal))
    story.append(Spacer(1, 12))

    if domain_scores:
        story.append(Paragraph("Domain Scores", heading))
        rows = [
            [
                Paragraph("Domain", table_header),
                Paragraph("Score", table_header),
                Paragraph("Maturity", table_header),
            ]
        ]

        for domain, score in domain_scores.items():
            rows.append([
                Paragraph(str(domain), table_cell),
                Paragraph(f"{score:.1f}", table_cell),
                Paragraph(get_maturity_level(score), table_cell),
            ])

        table = Table(rows, colWidths=[220, 70, 110], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f3f3f3")]),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    if export_mode == "Executive":
        intro = (management_content.get("intro") or "").strip()
        top_actions = management_content.get("top_actions", [])
        domain_blocks = management_content.get("domain_blocks", {})

        if intro:
            story.append(Paragraph(intro, normal))
            story.append(Spacer(1, 10))

        story.append(Paragraph("Top 5 Priority Actions", heading))
        if top_actions:
            for item in top_actions[:5]:
                if str(item).strip():
                    story.append(Paragraph(f"• {item}", bullet_style))
        else:
            story.append(Paragraph("-", normal))

        story.append(Spacer(1, 10))
        story.append(Paragraph("Key Areas of Improvement", heading))
        if domain_blocks:
            for domain, bullets in domain_blocks.items():
                story.append(Paragraph(f"<b>{domain}</b>", normal))
                for bullet in bullets:
                    if str(bullet).strip():
                        story.append(Paragraph(f"• {bullet}", bullet_style))
                story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("-", normal))

    else:
        story.append(Paragraph("Recommendations", heading))
        if recommendations:
            rows = [[
                Paragraph("Domain", table_header),
                Paragraph("Risk", table_header),
                Paragraph("Recommendation", table_header),
                Paragraph("Status", table_header),
                Paragraph("Responsible", table_header),
                Paragraph("Deadline", table_header),
            ]]

            for r in recommendations:
                rows.append([
                    Paragraph(str(r.get("domain_name", "") or ""), table_cell),
                    Paragraph(str(r.get("risk", "") or ""), table_cell),
                    Paragraph(str(r.get("text", "") or ""), table_cell),
                    Paragraph(str(r.get("status", "") or ""), table_cell),
                    Paragraph(str(r.get("responsible", "") or ""), table_cell),
                    Paragraph(str(r.get("deadline", "") or ""), table_cell),
                ])

            rec_table = Table(rows, colWidths=[90, 45, 190, 55, 95, 60], repeatRows=1)
            rec_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
            ]))
            story.append(rec_table)
        else:
            story.append(Paragraph("-", normal))

    if export_mode == "Detailed":
        story.append(Spacer(1, 12))
        story.append(Paragraph("Assessment Details", heading))
        if responses:
            if include_proof:
                rows = [[
                    Paragraph("Domain", table_header),
                    Paragraph("Question", table_header),
                    Paragraph("Answer", table_header),
                    Paragraph("Score", table_header),
                    Paragraph("Notes", table_header),
                    Paragraph("Proof", table_header),
                ]]
                col_widths = [70, 130, 55, 40, 110, 90]
            else:
                rows = [[
                    Paragraph("Domain", table_header),
                    Paragraph("Question", table_header),
                    Paragraph("Answer", table_header),
                    Paragraph("Score", table_header),
                    Paragraph("Notes", table_header),
                ]]
                col_widths = [80, 160, 60, 40, 165]

            for r in responses:
                base = [
                    Paragraph(str(r.get("domain", "") or ""), table_cell),
                    Paragraph(str(r.get("question", "") or ""), table_cell),
                    Paragraph(str(r.get("answer_value", "") or ""), table_cell),
                    Paragraph(str(r.get("score", "") or ""), table_cell),
                    Paragraph(str(r.get("notes", "") or ""), table_cell),
                ]
                if include_proof:
                    base.append(Paragraph(str(r.get("proof", "") or ""), table_cell))
                rows.append(base)

            details_table = Table(rows, colWidths=col_widths, repeatRows=1)
            details_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(details_table)
        else:
            story.append(Paragraph("-", normal))

    if include_mapping:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Control Mapping", heading))
        if mapping_rows:
            rows = [[
                Paragraph("Domain", table_header),
                Paragraph("Question", table_header),
                Paragraph("ISO 27001", table_header),
                Paragraph("NIST CSF", table_header),
                Paragraph("CIS", table_header),
                Paragraph("NIS2", table_header),
            ]]
            for r in mapping_rows:
                rows.append([
                    Paragraph(r["domain"], table_cell),
                    Paragraph(r["question"], table_cell),
                    Paragraph(r["iso27001"], table_cell),
                    Paragraph(r["nist_csf"], table_cell),
                    Paragraph(r["cis_control"], table_cell),
                    Paragraph(r["nis2"], table_cell),
                ])

            map_table = Table(
                rows,
                colWidths=[70, 150, 70, 70, 45, 90],
                repeatRows=1,
            )
            map_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(map_table)
        else:
            story.append(Paragraph("-", normal))

    doc.build(story)
    buffer.seek(0)
    return buffer
