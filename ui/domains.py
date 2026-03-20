import os
from pathlib import Path

import streamlit as st

from auth import user_can_edit
from db import upsert_answer, get_answers_for_assessment
from utils import (
    localize,
    safe_score_label_from_value,
    get_score_from_single_choice,
)

UPLOAD_DIR = Path("uploads")


def save_uploaded_proof(assessment_id: int, question_id: str, uploaded_file):
    if uploaded_file is None:
        return ""
    folder = UPLOAD_DIR / str(assessment_id)
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{question_id}_{uploaded_file.name}"
    file_path = folder / filename
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(file_path)


def ensure_domain_state_loaded(assessment_id: int, filtered_domains: list, score_map: dict):
    current_loaded = st.session_state.get("_loaded_assessment_id")
    if current_loaded == assessment_id:
        return

    saved_answers = get_answers_for_assessment(assessment_id)

    for domain in filtered_domains:
        for q in domain["questions"]:
            qid = q["id"]
            saved = saved_answers.get(qid)
            answer_type = q.get("answer_type", "score")

            if saved:
                if answer_type == "single_choice":
                    st.session_state[f"answer_value_{qid}"] = saved.get("answer_value", "")
                else:
                    st.session_state[f"score_{qid}"] = safe_score_label_from_value(saved.get("score"), score_map)

                st.session_state[f"notes_{qid}"] = saved.get("notes", "")
                st.session_state[f"proof_path_{qid}"] = saved.get("proof", "")
            else:
                st.session_state.setdefault(f"score_{qid}", "NotApplicable")
                st.session_state.setdefault(f"answer_value_{qid}", "")
                st.session_state.setdefault(f"notes_{qid}", "")
                st.session_state.setdefault(f"proof_path_{qid}", "")

    st.session_state["_loaded_assessment_id"] = assessment_id


def render_question_metadata(question, lang: str):
    cols = st.columns(4)
    cols[0].caption(f"Weight: {question.get('weight', 1)}")
    cols[1].caption(f"Risk: {question.get('risk', 'Medium')}")
    cols[2].caption(f"Priority: {question.get('remediation_priority', '-')}")
    cols[3].caption(f"Owner: {question.get('default_owner_role', '-')}")

    with st.expander("Evidence / Mapping / Context", expanded=False):
        evidence = question.get("evidence_examples", {})
        artifacts = question.get("expected_artifacts", {})
        applies = question.get("applies_to", [])
        scope = question.get("scope", [])
        iso = question.get("iso27001", [])
        nist = question.get("nist_csf", [])
        cis = question.get("cis_control", [])
        nis2 = question.get("nis2", [])
        family = question.get("control_family", "-")
        effort = question.get("effort", "-")
        impact = question.get("business_impact", "-")

        st.markdown(f"**Control family:** {family}")
        st.markdown(f"**Effort:** {effort}")
        st.markdown(f"**Business impact:** {impact}")
        st.markdown(f"**Applies to:** {', '.join(applies) if applies else '-'}")
        st.markdown(f"**Scope:** {', '.join(scope) if scope else '-'}")
        st.markdown(f"**ISO 27001:** {', '.join(iso) if iso else '-'}")
        st.markdown(f"**NIST CSF:** {', '.join(nist) if nist else '-'}")
        st.markdown(f"**CIS Controls:** {', '.join(cis) if cis else '-'}")
        st.markdown(f"**NIS2:** {', '.join(nis2) if nis2 else '-'}")

        ev = evidence.get(lang) if isinstance(evidence, dict) else evidence
        art = artifacts.get(lang) if isinstance(artifacts, dict) else artifacts

        if ev:
            st.markdown("**Evidence examples**")
            for item in ev:
                st.write(f"- {item}")

        if art:
            st.markdown("**Expected artifacts**")
            for item in art:
                st.write(f"- {item}")


def set_domain_not_applicable(domain):
    for q in domain["questions"]:
        qid = q["id"]
        answer_type = q.get("answer_type", "score")
        if answer_type == "single_choice":
            st.session_state[f"answer_value_{qid}"] = ""
        else:
            st.session_state[f"score_{qid}"] = "NotApplicable"


def clear_domain_answers(domain):
    for q in domain["questions"]:
        qid = q["id"]
        answer_type = q.get("answer_type", "score")
        if answer_type == "single_choice":
            st.session_state[f"answer_value_{qid}"] = ""
        else:
            st.session_state[f"score_{qid}"] = "NotApplicable"

        st.session_state[f"notes_{qid}"] = ""
        st.session_state[f"proof_path_{qid}"] = ""


def get_domain_saved_count(assessment_id: int, domain):
    saved_answers = get_answers_for_assessment(assessment_id)
    domain_question_ids = {q["id"] for q in domain["questions"]}
    count = 0
    for qid, row in saved_answers.items():
        if qid in domain_question_ids and row.get("score") is not None:
            count += 1
    return count, len(domain_question_ids)


def render_domain_form(data, lang, assessment, domain):
    domain_name = localize(domain["name"], lang)
    st.header(domain_name)

    saved_count, total_count = get_domain_saved_count(assessment["id"], domain)
    st.caption(f"Saved answers in this domain: {saved_count}/{total_count}")

    top1, top2, top3 = st.columns([1, 1, 3])

    with top1:
        if st.button(
            "Set all NotApplicable",
            key=f"set_na_{domain['id']}",
            disabled=not user_can_edit(),
            help="Sets all questions in this domain to NotApplicable in the UI. Save each answer you want persisted.",
        ):
            set_domain_not_applicable(domain)
            st.rerun()

    with top2:
        if st.button(
            "Clear domain",
            key=f"clear_domain_{domain['id']}",
            disabled=not user_can_edit(),
            help="Clears score, notes and proof path in the UI for all questions in this domain.",
        ):
            clear_domain_answers(domain)
            st.rerun()

    with top3:
        st.info(
            "Tip: Use 'Set all NotApplicable' for domains that do not apply, then save only the answers you want persisted in DB."
        )

    for q in domain["questions"]:
        qid = q["id"]
        q_text = localize(q["text"], lang)
        answer_type = q.get("answer_type", "score")

        st.subheader(q_text)
        render_question_metadata(q, lang)

        col1, col2 = st.columns([2, 3])

        selected_score = None
        answer_value = ""

        with col1:
            if answer_type == "single_choice":
                options = q.get("options", {}).get(lang) or q.get("options", {}).get("en") or []
                current_value = st.session_state.get(f"answer_value_{qid}", options[0] if options else "")
                selected_option = st.selectbox(
                    "Answer",
                    options if options else [""],
                    index=options.index(current_value) if options and current_value in options else 0,
                    key=f"answer_value_{qid}",
                )
                answer_value = selected_option
                selected_score = get_score_from_single_choice(q, selected_option)
                st.caption(f"Calculated score: {selected_score if selected_score is not None else 'N/A'}")
            else:
                st.selectbox(
                    "Score",
                    list(data["meta"]["scoring"].keys()),
                    key=f"score_{qid}",
                )
                selected_label = st.session_state.get(f"score_{qid}", "NotApplicable")
                selected_score = data["meta"]["scoring"].get(selected_label)
                answer_value = selected_label

            proof_file = st.file_uploader(
                "Proof image",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"upload_{qid}",
            )

        with col2:
            st.text_area(
                "Observatii / dovezi",
                key=f"notes_{qid}",
                height=100,
            )

        saved_proof_path = st.session_state.get(f"proof_path_{qid}", "")
        if saved_proof_path:
            st.caption(f"Saved proof: {saved_proof_path}")
            if os.path.exists(saved_proof_path):
                try:
                    st.image(saved_proof_path, width=320)
                except Exception:
                    st.caption("Nu am putut afisa imaginea salvata.")

        if st.button(f"Salveaza raspuns {qid}", key=f"save_{qid}", disabled=not user_can_edit()):
            proof_path = saved_proof_path
            if proof_file is not None:
                proof_path = save_uploaded_proof(assessment["id"], qid, proof_file)
                st.session_state[f"proof_path_{qid}"] = proof_path

            upsert_answer(
                assessment_id=assessment["id"],
                domain_id=domain["id"],
                domain_name=domain_name,
                question_id=qid,
                question_text=q_text,
                answer_value=answer_value,
                score=selected_score,
                notes=st.session_state.get(f"notes_{qid}", ""),
                proof=proof_path,
            )
            st.success("Raspuns salvat.")
