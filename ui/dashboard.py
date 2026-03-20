import pandas as pd
import streamlit as st

from db import get_answers_for_assessment, get_assessments_for_company
from utils import (
    build_question_index,
    calculate_overall_score,
    calculate_scores,
    calculate_evidence_completeness,
    generate_bar_chart,
    generate_heatmap,
    generate_trend_chart,
    get_maturity_level,
    render_progress_bar_html,
    score_to_hex,
)


def render_dashboard_section(data, lang, company, assessment, assessment_state):
    responses = assessment_state["responses_saved"]
    filtered_domains = assessment_state.get("filtered_domains", data["domains"])
    question_index = build_question_index(data)

    domain_scores = calculate_scores(responses)
    overall_score = calculate_overall_score(domain_scores)
    evidence_stats = calculate_evidence_completeness(responses)

    answered_count = len(responses)
    total_count = sum(len(d["questions"]) for d in filtered_domains)
    overall_maturity = get_maturity_level(overall_score)

    st.header("Executive Dashboard")
    st.caption(
        "Trend pe Evaluari reprezinta evolutia scorului general in timp pentru toate evaluarile salvate ale aceleiasi companii."
    )

    if filtered_domains != data["domains"]:
        st.info("Dashboard is showing only questions matching the current filters.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Overall score", f"{overall_score:.1f}/100")
    c2.metric("Maturity", overall_maturity)
    c3.metric("Saved answers", f"{answered_count}/{total_count}")

    st.subheader("Evidence Completeness")
    e1, e2, e3 = st.columns(3)
    e1.metric("With notes", f"{evidence_stats['with_notes']}/{evidence_stats['scored_answers']}", f"{evidence_stats['notes_pct']}%")
    e2.metric("With proof", f"{evidence_stats['with_proof']}/{evidence_stats['scored_answers']}", f"{evidence_stats['proof_pct']}%")
    e3.metric("With notes + proof", f"{evidence_stats['with_notes_and_proof']}/{evidence_stats['scored_answers']}", f"{evidence_stats['complete_pct']}%")

    st.subheader("Domain Scores")
    if domain_scores:
        for domain_name, score in domain_scores.items():
            st.markdown(
                render_progress_bar_html(domain_name, score, get_maturity_level(score)),
                unsafe_allow_html=True,
            )
    else:
        st.info("Nu exista scoruri calculate inca. Salveaza raspunsurile din Assessment.")

    if domain_scores:
        df_scores = pd.DataFrame(
            [
                {
                    "Domain": domain_name,
                    "Score": round(score, 1),
                    "Maturity": get_maturity_level(score),
                }
                for domain_name, score in domain_scores.items()
            ]
        )

        def color_score(val):
            try:
                val = float(val)
            except Exception:
                return ""
            color = score_to_hex(val)
            text_color = "#ffffff" if val < 55 else "#111111"
            return f"background-color: {color}; color: {text_color};"

        st.dataframe(
            df_scores.style.map(color_score, subset=["Score"]),
            use_container_width=True,
        )

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader("Bar chart")
            st.image(generate_bar_chart(domain_scores), use_container_width=True)
        with chart_col2:
            st.subheader("Heatmap")
            st.image(generate_heatmap(domain_scores), use_container_width=True)

    assessments = get_assessments_for_company(company["id"])
    trend_rows = []

    for a in reversed(assessments):
        answer_rows = get_answers_for_assessment(a["id"])
        trend_responses = []

        for qid, row in answer_rows.items():
            meta = question_index.get(qid)
            if not meta:
                continue

            score = row.get("score")
            if score is None:
                continue

            trend_responses.append({
                "domain": row.get("domain_name"),
                "score": score,
                "weight": meta.get("weight", 1),
            })

        trend_scores = calculate_scores(trend_responses)
        trend_rows.append({
            "Assessment": a["name"],
            "Date": a["date"],
            "Overall": round(calculate_overall_score(trend_scores), 1),
        })

    if trend_rows:
        st.subheader("Trend pe evaluari")
        df_trend = pd.DataFrame(trend_rows)
        st.dataframe(df_trend, use_container_width=True)
        st.image(generate_trend_chart(df_trend), use_container_width=True)
