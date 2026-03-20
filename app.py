import json
import streamlit as st

from auth import render_auth_sidebar, user_is_admin
from db import init_db, get_answers_for_assessment
from ui.company import render_company_section, render_admin_user_section
from ui.assessment import render_assessment_section
from ui.dashboard import render_dashboard_section
from ui.executive import render_executive_section
from ui.import_export import render_import_export_section
from utils import collect_filter_values

APP_TITLE = "GRC Assessment Tool"


def load_questions():
    with open("assessment_questions.json", "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    st.set_page_config(layout="wide", page_title=APP_TITLE)
    init_db()

    data = load_questions()
    user = render_auth_sidebar()
    if not user:
        st.stop()

    st.sidebar.title(APP_TITLE)
    lang = st.sidebar.selectbox("Language", ["ro", "en"], index=1)

    applies_values, scope_values = collect_filter_values(data)

    selected_applies = st.sidebar.multiselect(
        "Filter by Applies To",
        applies_values,
        default=[],
        help="Leave empty to include all questions.",
    )

    selected_scope = st.sidebar.multiselect(
        "Filter by Scope",
        scope_values,
        default=[],
        help="Leave empty to include all questions.",
    )

    if user_is_admin():
        render_admin_user_section()

    context = render_company_section(user=user, lang=lang)
    if not context:
        st.info("Selecteaza sau creeaza o companie si o evaluare.")
        st.stop()

    saved_answers = get_answers_for_assessment(context["assessment"]["id"])
    saved_count = len(saved_answers)
    total_questions = sum(len(d["questions"]) for d in data["domains"])

    st.title("Cyber Security Assessment")
    st.caption(
        f"Company: {context['company']['name']} | "
        f"Assessment: {context['assessment']['name']} | "
        f"Date: {context['assessment']['date']} | "
        f"Saved answers: {saved_count}/{total_questions}"
    )

    tabs = st.tabs([
        "Assessment",
        "Executive Dashboard",
        "Executive Summary",
        "Import / Export",
    ])

    with tabs[0]:
        assessment_state = render_assessment_section(
            data=data,
            lang=lang,
            user=user,
            company=context["company"],
            assessment=context["assessment"],
            selected_applies=selected_applies,
            selected_scope=selected_scope,
        )

    with tabs[1]:
        render_dashboard_section(
            data=data,
            lang=lang,
            company=context["company"],
            assessment=context["assessment"],
            assessment_state=assessment_state,
        )

    with tabs[2]:
        render_executive_section(
            data=data,
            lang=lang,
            user=user,
            company=context["company"],
            assessment=context["assessment"],
            assessment_state=assessment_state,
        )

    with tabs[3]:
        render_import_export_section(
            data=data,
            lang=lang,
            user=user,
            company=context["company"],
            assessment=context["assessment"],
            assessment_state=assessment_state,
        )


if __name__ == "__main__":
    main()
