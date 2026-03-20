import streamlit as st

from db import (
    create_company,
    get_companies,
    get_assessments_for_company,
    get_assessment_details,
    create_assessment,
    list_users,
    create_user,
)
from auth import user_can_edit


def render_admin_user_section():
    with st.sidebar.expander("User management", expanded=False):
        st.write("Utilizatori existenti")
        users = list_users()
        for user in users:
            st.caption(f"{user['username']} ({user['role']})")

        st.write("---")
        new_user = st.text_input("New username", key="new_user")
        new_pass = st.text_input("New password", type="password", key="new_pass")
        new_role = st.selectbox("Role", ["admin", "auditor", "viewer"], key="new_role")

        if st.button("Create user"):
            if new_user.strip() and new_pass.strip():
                ok, msg = create_user(new_user.strip(), new_pass.strip(), new_role)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


def render_company_section(user, lang):
    companies = get_companies()

    with st.sidebar.expander("Companies", expanded=True):
        if user_can_edit():
            new_company = st.text_input("Companie noua")
            if st.button("Adauga companie"):
                if new_company.strip():
                    create_company(new_company.strip())
                    st.success("Companie adaugata.")
                    st.rerun()

    if not companies:
        return None

    selected_company_name = st.sidebar.selectbox(
        "Selecteaza companie",
        [c["name"] for c in companies],
    )
    selected_company = next(c for c in companies if c["name"] == selected_company_name)

    st.sidebar.write("---")
    st.sidebar.subheader("Assessment")

    assessments = get_assessments_for_company(selected_company["id"])

    if assessments:
        options = {f"{a['name']} | {a['date']} | id={a['id']}": a["id"] for a in assessments}
        selected_label = st.sidebar.selectbox("Evaluari existente", list(options.keys()))
        if st.sidebar.button("Incarca evaluarea"):
            st.session_state["assessment_id"] = options[selected_label]
            st.session_state.pop("_loaded_assessment_id", None)
            st.rerun()
    else:
        st.sidebar.info("Nu exista evaluari pentru compania selectata.")

    if user_can_edit():
        new_assessment_name = st.sidebar.text_input("Evaluare noua")
        if st.sidebar.button("Creeaza evaluare noua"):
            if new_assessment_name.strip():
                aid = create_assessment(
                    company_id=selected_company["id"],
                    user_id=user["id"],
                    name=new_assessment_name.strip(),
                )
                st.session_state["assessment_id"] = aid
                st.session_state.pop("_loaded_assessment_id", None)
                st.success("Evaluare creata.")
                st.rerun()

    if "assessment_id" not in st.session_state:
        return None

    assessment = get_assessment_details(st.session_state["assessment_id"])
    if not assessment:
        return None

    return {
        "company": selected_company,
        "assessment": assessment,
    }
