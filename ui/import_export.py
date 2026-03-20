import json
import pandas as pd
import streamlit as st

from auth import user_can_edit
from db import get_executive_summary, get_recommendations
from json_io import export_assessment_package, import_assessment_package
from utils import (
    calculate_overall_score,
    calculate_scores,
    generate_pdf,
    build_question_index,
    build_mapping_rows,
    sort_recommendations_by_risk,
    sort_recommendations_for_roadmap,
)
from word_report import generate_word_report


def render_import_export_section(data, lang, user, company, assessment, assessment_state):
    responses = assessment_state["responses_saved"]
    domain_scores = calculate_scores(responses)
    overall_score = calculate_overall_score(domain_scores)

    recommendations = sort_recommendations_by_risk(get_recommendations(assessment["id"]))
    summary = st.session_state.get("summary_text", get_executive_summary(assessment["id"]))
    question_index = build_question_index(data)
    mapping_rows = build_mapping_rows(responses, question_index, lang)

    st.header("Import / Export")
    st.caption("Exporturile includ doar raspunsurile salvate care nu sunt NotApplicable.")

    st.subheader("Export Options")

    col_opt1, col_opt2, col_opt3 = st.columns(3)

    with col_opt1:
        export_mode = st.selectbox(
            "Export mode",
            ["Executive", "Detailed"],
            index=0,
            help="Executive = strict necesar. Detailed = include mai multe detalii.",
        )

    with col_opt2:
        include_proof = st.checkbox(
            "Include Proof Image",
            value=False if export_mode == "Executive" else True,
        )

    with col_opt3:
        include_mapping = st.checkbox(
            "Include Control Mapping",
            value=False if export_mode == "Executive" else True,
        )

    if export_mode == "Executive":
        export_responses = [
            {
                "domain_id": r.get("domain_id"),
                "domain": r.get("domain"),
                "question_id": r.get("question_id"),
                "question": r.get("question"),
                "score": r.get("score"),
            }
            for r in responses
        ]
    else:
        export_responses = []
        for r in responses:
            row = dict(r)
            if not include_proof:
                row["proof"] = ""
            export_responses.append(row)

    export_mapping_rows = mapping_rows if include_mapping else []

    package = export_assessment_package(
        company_name=company["name"],
        assessment_name=assessment["name"],
        assessment_date=assessment["date"],
        language=lang,
        scores=domain_scores,
        summary=summary,
        answers=export_responses,
        recommendations=recommendations,
        mapping_rows=export_mapping_rows,
        include_proof=include_proof,
        include_mapping=include_mapping,
        export_mode=export_mode,
    )

    st.subheader("Export")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.download_button(
            "Export JSON",
            data=json.dumps(package, ensure_ascii=False, indent=2),
            file_name=f"{company['name']}_{assessment['name']}.json",
            mime="application/json",
        )

    with c2:
        pdf_buffer = generate_pdf(
            company_name=company["name"],
            assessment_name=assessment["name"],
            assessment_date=assessment["date"],
            overall_score=overall_score,
            domain_scores=domain_scores,
            summary=summary,
            recommendations=recommendations,
            mapping_rows=export_mapping_rows,
            responses=export_responses,
            include_proof=include_proof,
            include_mapping=include_mapping,
            export_mode=export_mode,
        )
        st.download_button(
            "Export PDF",
            data=pdf_buffer,
            file_name=f"{company['name']}_{assessment['name']}.pdf",
            mime="application/pdf",
        )

    with c3:
        word_buffer = generate_word_report(
            company_name=company["name"],
            assessment_name=assessment["name"],
            assessment_date=assessment["date"],
            overall_score=overall_score,
            domain_scores=domain_scores,
            summary=summary,
            recommendations=recommendations,
            mapping_rows=export_mapping_rows,
            responses=export_responses,
            include_proof=include_proof,
            include_mapping=include_mapping,
            export_mode=export_mode,
        )
        st.download_button(
            "Export Word",
            data=word_buffer,
            file_name=f"{company['name']}_{assessment['name']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    with c4:
        roadmap_df = pd.DataFrame([
            {
                "Risk": r.get("risk", ""),
                "Owner": r.get("responsible", "") or "",
                "Deadline": r.get("deadline", "") or "",
                "Domain": r.get("domain_name", ""),
                "Recommendation": r.get("text", ""),
                "Status": r.get("status", ""),
                "Source": r.get("source", ""),
            }
            for r in sort_recommendations_for_roadmap(recommendations)
        ])
        csv_data = roadmap_df.to_csv(index=False)
        st.download_button(
            "Export Roadmap CSV",
            data=csv_data,
            file_name=f"{company['name']}_{assessment['name']}_roadmap.csv",
            mime="text/csv",
        )

    st.subheader("Import JSON")
    imported_name = st.text_input("Nume evaluare importata")
    uploaded_json = st.file_uploader("Selecteaza fisier JSON", type=["json"])

    if st.button("Import assessment", disabled=not user_can_edit()):
        if uploaded_json is None:
            st.warning("Selecteaza un fisier JSON.")
        else:
            try:
                payload = json.load(uploaded_json)
                new_name = imported_name.strip() or f"{payload.get('assessment_name', 'Imported Assessment')} (Imported)"
                new_aid = import_assessment_package(
                    payload=payload,
                    company_id=company["id"],
                    user_id=user["id"],
                    assessment_name=new_name,
                )
                st.session_state["assessment_id"] = new_aid
                st.session_state.pop("_loaded_assessment_id", None)
                st.success("Import realizat cu succes.")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")
