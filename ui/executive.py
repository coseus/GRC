from datetime import date

import pandas as pd
import streamlit as st

from ai import generate_executive_summary
from auth import user_can_edit
from db import (
    get_executive_summary,
    save_executive_summary,
    get_recommendations,
    add_recommendation,
    update_recommendation,
    delete_recommendation,
)
from utils import (
    calculate_overall_score,
    calculate_scores,
    localize,
    build_question_index,
    sort_recommendations_by_risk,
)


def build_generated_recommendations_from_saved(data, lang, responses):
    question_index = build_question_index(data)
    recommendations = []

    for response in responses:
        qid = response.get("question_id")
        score = response.get("score")
        meta = question_index.get(qid, {})
        if score is None or not meta:
            continue

        if score in (0, 50):
            recommendations.append({
                "domain_id": response.get("domain_id"),
                "domain_name": response.get("domain"),
                "text": localize(meta.get("recommendation", {"en": "No recommendation defined"}), lang),
                "risk": meta.get("risk", "Medium"),
                "status": "Open",
                "source": "auto",
            })

    return recommendations


def recommendation_exists(existing_recos, domain_name, text):
    for r in existing_recos:
        if r.get("domain_name") == domain_name and r.get("text") == text:
            return True
    return False


def risk_style(risk: str) -> str:
    if risk == "Critical":
        return "background-color:#b71c1c;color:white;"
    if risk == "High":
        return "background-color:#e65100;color:white;"
    if risk == "Medium":
        return "background-color:#f9a825;color:black;"
    if risk == "Low":
        return "background-color:#2e7d32;color:white;"
    return ""


def status_style(status: str) -> str:
    if status == "Open":
        return "background-color:#d32f2f;color:white;"
    if status == "In Progress":
        return "background-color:#f9a825;color:black;"
    if status == "Done":
        return "background-color:#2e7d32;color:white;"
    if status == "Rejected":
        return "background-color:#616161;color:white;"
    return ""


def render_recommendation_summary_table(recommendations):
    if not recommendations:
        st.info("No recommendations yet.")
        return

    rows = []
    for r in recommendations:
        rows.append({
            "Domain": r.get("domain_name", ""),
            "Risk": r.get("risk", ""),
            "Recommendation": r.get("text", ""),
            "Status": r.get("status", ""),
            "Owner": r.get("responsible", "") or "",
            "Deadline": r.get("deadline", "") or "",
            "Source": r.get("source", "").upper(),
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df.style.map(risk_style, subset=["Risk"]).map(status_style, subset=["Status"]),
        use_container_width=True,
    )


def render_executive_section(data, lang, user, company, assessment, assessment_state):
    responses = assessment_state["responses_saved"]
    domain_scores = calculate_scores(responses)
    overall_score = calculate_overall_score(domain_scores)

    st.header("Executive Summary")

    if "summary_text" not in st.session_state:
        st.session_state["summary_text"] = get_executive_summary(assessment["id"])

    if "generated_summary_text" not in st.session_state:
        st.session_state["generated_summary_text"] = ""

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Genereaza AI Executive Summary"):
            st.session_state["generated_summary_text"] = generate_executive_summary(
                company_name=company["name"],
                assessment_name=assessment["name"],
                overall_score=overall_score,
                domain_scores=domain_scores,
                lang=lang,
            )
            st.rerun()

    with c2:
        if st.button("Aplica textul AI"):
            generated = st.session_state.get("generated_summary_text", "").strip()
            if generated:
                st.session_state["summary_text"] = generated
                st.rerun()
            else:
                st.warning("Nu exista un text AI generat.")

    with c3:
        if st.button("Salveaza Executive Summary", disabled=not user_can_edit()):
            save_executive_summary(
                assessment["id"],
                st.session_state.get("summary_text", "")
            )
            st.success("Executive Summary salvat.")

    generated = st.session_state.get("generated_summary_text", "")
    if generated:
        st.subheader("AI Generated Draft")
        st.text_area(
            "Draft generat de AI",
            value=generated,
            height=180,
            key="generated_summary_preview",
            disabled=True,
        )

    st.text_area("Summary", key="summary_text", height=220)

    st.subheader("Recommendations")

    col_gen1, col_gen2 = st.columns([2, 3])

    with col_gen1:
        if st.button("Generate Recommendations from Assessment", disabled=not user_can_edit()):
            generated_recos = build_generated_recommendations_from_saved(data, lang, responses)
            existing_recos = get_recommendations(assessment["id"])

            added = 0
            for reco in generated_recos:
                if not recommendation_exists(existing_recos, reco["domain_name"], reco["text"]):
                    add_recommendation(
                        assessment_id=assessment["id"],
                        domain_id=reco["domain_id"],
                        domain_name=reco["domain_name"],
                        text=reco["text"],
                        risk=reco["risk"],
                        source="auto",
                        responsible="",
                        deadline=None,
                        status="Open",
                    )
                    added += 1

            st.success(f"{added} recommendations added.")
            st.rerun()

    with col_gen2:
        st.caption(
            "Recomandarile sunt generate automat din raspunsurile salvate pentru scoruri Fail / Partial, "
            "apoi pot fi editate, sterse sau completate manual."
        )

    st.subheader("Add Recommendation")

    with st.form("add_reco_form", clear_on_submit=True):
        add_domain = st.selectbox(
            "Domain",
            [localize(d["name"], lang) for d in data["domains"]],
        )
        add_text = st.text_area("Recommendation")
        add_risk = st.selectbox("Risk", ["Low", "Medium", "High", "Critical"])
        add_responsible = st.text_input("Responsible")
        add_deadline = st.date_input("Deadline", value=None)
        add_status = st.selectbox("Status", ["Open", "In Progress", "Done", "Rejected"])

        submitted = st.form_submit_button("Add Recommendation", disabled=not user_can_edit())
        if submitted:
            add_domain_obj = next(
                d for d in data["domains"] if localize(d["name"], lang) == add_domain
            )
            add_recommendation(
                assessment_id=assessment["id"],
                domain_id=add_domain_obj["id"],
                domain_name=add_domain,
                text=add_text,
                risk=add_risk,
                source="manual",
                responsible=add_responsible,
                deadline=str(add_deadline) if add_deadline else None,
                status=add_status,
            )
            st.success("Recommendation added.")
            st.rerun()

    st.subheader("Recommendation Table")
    recommendations = sort_recommendations_by_risk(get_recommendations(assessment["id"]))

    render_recommendation_summary_table(recommendations)

    if recommendations:
        st.subheader("Edit / Delete")
        for reco in recommendations:
            source_label = reco.get("source", "manual").upper()
            with st.expander(
                f"{reco['domain_name']} | {reco['risk']} | {reco['status']} | {source_label}",
                expanded=False,
            ):
                edit_text = st.text_area(
                    "Recommendation",
                    value=reco["text"],
                    key=f"edit_text_{reco['id']}",
                    height=100,
                )

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    edit_risk = st.selectbox(
                        "Risk",
                        ["Low", "Medium", "High", "Critical"],
                        index=["Low", "Medium", "High", "Critical"].index(reco["risk"]),
                        key=f"edit_risk_{reco['id']}",
                    )
                with col_b:
                    edit_responsible = st.text_input(
                        "Responsible",
                        value=reco.get("responsible", "") or "",
                        key=f"edit_resp_{reco['id']}",
                    )
                with col_c:
                    status_options = ["Open", "In Progress", "Done", "Rejected"]
                    edit_status = st.selectbox(
                        "Status",
                        status_options,
                        index=status_options.index(reco["status"]),
                        key=f"edit_status_{reco['id']}",
                    )

                current_deadline = reco.get("deadline")
                parsed_deadline = date.fromisoformat(current_deadline) if current_deadline else None
                edit_deadline = st.date_input(
                    "Deadline",
                    value=parsed_deadline,
                    key=f"edit_deadline_{reco['id']}",
                )

                c_upd, c_del = st.columns(2)
                with c_upd:
                    if st.button("Update", key=f"upd_{reco['id']}", disabled=not user_can_edit()):
                        update_recommendation(
                            reco_id=reco["id"],
                            text=edit_text,
                            risk=edit_risk,
                            responsible=edit_responsible,
                            deadline=str(edit_deadline) if edit_deadline else None,
                            status=edit_status,
                        )
                        st.success("Recommendation updated.")
                        st.rerun()

                with c_del:
                    if st.button("Delete", key=f"del_{reco['id']}", disabled=not user_can_edit()):
                        delete_recommendation(reco["id"])
                        st.success("Recommendation deleted.")
                        st.rerun()
    else:
        st.info("No recommendations yet. Generate them from the assessment or add them manually.")
