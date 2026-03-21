import streamlit as st

from db import (
    create_company,
    get_companies,
    get_assessments_for_company,
    get_assessment_details,
    create_assessment,
    list_users,
    create_user,
    update_user,
    update_user_password,
    delete_user,
)
from auth import user_can_edit


def render_admin_user_section():
    with st.sidebar.expander("User management", expanded=False):
        st.write("Utilizatori existenti")
        users = list_users()

        for user in users:
            active_label = "Active" if user["is_active"] else "Inactive"
            st.caption(f"{user['username']} ({user['role']}) - {active_label}")

        st.write("---")
        st.subheader("Create user")

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

        st.write("---")
        st.subheader("Edit / Delete user")

        if users:
            user_options = {
                f"{u['username']} ({u['role']}){' - inactive' if not u['is_active'] else ''}": u
                for u in users
            }
            selected_label = st.selectbox("Select user", list(user_options.keys()), key="selected_user_admin")
            selected_user = user_options[selected_label]

            edit_username = st.text_input(
                "Edit username",
                value=selected_user["username"],
                key=f"edit_username_{selected_user['id']}",
            )
            edit_role = st.selectbox(
                "Edit role",
                ["admin", "auditor", "viewer"],
                index=["admin", "auditor", "viewer"].index(selected_user["role"]),
                key=f"edit_role_{selected_user['id']}",
            )
            edit_active = st.checkbox(
                "Active",
                value=bool(selected_user["is_active"]),
                key=f"edit_active_{selected_user['id']}",
            )

            new_password = st.text_input(
                "New password (leave empty to keep current)",
                type="password",
                key=f"edit_password_{selected_user['id']}",
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Update user", key=f"btn_update_user_{selected_user['id']}"):
                    ok, msg = update_user(
                        user_id=selected_user["id"],
                        username=edit_username.strip(),
                        role=edit_role,
                        is_active=edit_active,
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            with col2:
                if st.button("Change password", key=f"btn_change_password_{selected_user['id']}"):
                    if new_password.strip():
                        ok, msg = update_user_password(selected_user["id"], new_password.strip())
                        if ok:
                            st.success(msg)
                            st.rerun()
                    else:
                        st.warning("Enter a new password.")

            with col3:
                if st.button("Delete user", key=f"btn_delete_user_{selected_user['id']}"):
                    if selected_user["username"] == "admin":
                        st.error("Default admin user cannot be deleted.")
                    else:
                        ok, msg = delete_user(selected_user["id"])
                        if ok:
                            st.success(msg)
                            st.rerun()


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
