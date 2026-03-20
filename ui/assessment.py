import streamlit as st

from db import get_answers_for_assessment
from ui.domains import ensure_domain_state_loaded, render_domain_form
from utils import localize, filter_domains


def collect_saved_responses(filtered_domains, lang, assessment_id):
    saved_answers = get_answers_for_assessment(assessment_id)
    responses = []

    for domain in filtered_domains:
        domain_name = localize(domain["name"], lang)
        for q in domain["questions"]:
            qid = q["id"]
            if qid not in saved_answers:
                continue

            row = saved_answers[qid]
            score = row.get("score")
            if score is None:
                continue

            responses.append({
                "domain_id": domain["id"],
                "domain": domain_name,
                "question_id": qid,
                "question": localize(q["text"], lang),
                "answer_value": row.get("answer_value", ""),
                "score": score,
                "weight": q.get("weight", 1),
                "risk": q.get("risk", "Medium"),
                "notes": row.get("notes", ""),
                "proof": row.get("proof", ""),
            })

    return responses


def domain_has_answered_question(domain, assessment_id):
    saved_answers = get_answers_for_assessment(assessment_id)
    for q in domain["questions"]:
        row = saved_answers.get(q["id"])
        if row and row.get("score") is not None:
            return True
    return False


def render_assessment_section(data, lang, user, company, assessment, selected_applies, selected_scope):
    filtered_domains = filter_domains(data, selected_applies, selected_scope)

    if not filtered_domains:
        st.warning("No questions match the selected filters.")
        return {
            "responses_saved": [],
            "filtered_domains": [],
            "selected_domain_idx": 0,
        }

    ensure_domain_state_loaded(
        assessment_id=assessment["id"],
        filtered_domains=filtered_domains,
        score_map=data["meta"]["scoring"],
    )

    show_answered_only = st.checkbox(
        "Show only domains with saved answers",
        value=False,
        help="Hide domains where all questions are still NotApplicable or unsaved.",
    )

    visible_domains = filtered_domains
    if show_answered_only:
        visible_domains = [
            d for d in filtered_domains
            if domain_has_answered_question(d, assessment["id"])
        ]

    if not visible_domains:
        st.info("No domains with saved answers match the current filters.")
        return {
            "responses_saved": [],
            "filtered_domains": [],
            "selected_domain_idx": 0,
        }

    domain_labels = [localize(d["name"], lang) for d in visible_domains]
    default_idx = min(st.session_state.get("selected_domain_idx", 0), len(domain_labels) - 1)

    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

    with col_nav1:
        if st.button("Previous domain", disabled=default_idx <= 0):
            st.session_state["selected_domain_idx"] = max(0, default_idx - 1)
            st.rerun()

    with col_nav2:
        selected_label = st.selectbox(
            "Select domain",
            domain_labels,
            index=default_idx,
        )
        selected_idx = domain_labels.index(selected_label)
        st.session_state["selected_domain_idx"] = selected_idx

    with col_nav3:
        if st.button("Next domain", disabled=selected_idx >= len(domain_labels) - 1):
            st.session_state["selected_domain_idx"] = min(len(domain_labels) - 1, selected_idx + 1)
            st.rerun()

    domain = visible_domains[selected_idx]
    render_domain_form(data=data, lang=lang, assessment=assessment, domain=domain)

    return {
        "responses_saved": collect_saved_responses(filtered_domains, lang, assessment["id"]),
        "filtered_domains": filtered_domains,
        "selected_domain_idx": selected_idx,
    }
