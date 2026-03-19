import streamlit as st
import json
import pandas as pd
import sqlite3

from db import (
    init_db,
    create_company,
    get_companies,
    create_assessment,
    save_answer,
    get_assessment_scores,
    get_answers_for_assessment
)

from utils import calculate_scores, generate_chart, get_maturity_level, generate_pdf
from word_report import generate_word

DB_NAME = "assessment.db"  # definim aici daca nu e in db.py

# -------------------------
# INIT
# -------------------------
init_db()
st.set_page_config(layout="wide", page_title="GRC Assessment Tool")

# Load questions
with open("assessment_questions.json", encoding="utf-8") as f:
    data = json.load(f)

# -------------------------
# SIDEBAR - Companie + Limba
# -------------------------
st.sidebar.title("GRC Tool")

companies = get_companies()
company_names = [c[1] for c in companies]

new_company = st.sidebar.text_input("Companie noua")
if st.sidebar.button("Adauga companie") and new_company.strip():
    create_company(new_company.strip())
    st.rerun()

selected_company = st.sidebar.selectbox(
    "Selecteaza companie",
    company_names if company_names else ["Nicio companie inca"]
)

company_id = None
for cid, cname in companies:
    if cname == selected_company:
        company_id = cid
        break

lang = st.sidebar.selectbox("Limba", ["ro", "en"])

# -------------------------
# Functie evaluari per companie
# -------------------------
def get_assessments_for_company(cid):
    if not cid:
        return []
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT id, name 
        FROM assessments 
        WHERE company_id = ? 
        ORDER BY date DESC
    """, (cid,))
    data = c.fetchall()
    conn.close()
    return data

# -------------------------
# Selectie evaluare
# -------------------------
if company_id:
    assessments = get_assessments_for_company(company_id)
    
    if assessments:
        assessment_dict = {f"{a[1]} (id: {a[0]})": a[0] for a in assessments}
        options = ["Creeaza evaluare noua"] + list(assessment_dict.keys())
        
        selected_str = st.selectbox(
            "Evaluare existenta sau noua",
            options
        )
        
        if selected_str == "Creeaza evaluare noua":
            assessment_name = st.text_input("Nume evaluare noua")
            if st.button("Creeaza evaluare") and assessment_name.strip():
                new_id = create_assessment(company_id, assessment_name.strip())
                st.session_state.assessment_id = new_id
                st.success(f"Evaluare creata: {assessment_name}")
                st.rerun()
        else:
            selected_id = assessment_dict[selected_str]
            if "assessment_id" not in st.session_state or st.session_state.assessment_id != selected_id:
                st.session_state.assessment_id = selected_id
                st.info(f"Evaluare incarcata: {selected_str}")
                st.rerun()
    else:
        st.info("Nu exista evaluari pentru aceasta companie inca")
        assessment_name = st.text_input("Nume evaluare noua")
        if st.button("Creeaza prima evaluare") and assessment_name.strip():
            new_id = create_assessment(company_id, assessment_name.strip())
            st.session_state.assessment_id = new_id
            st.success(f"Evaluare creata: {assessment_name}")
            st.rerun()

    if st.button("Refresh lista evaluari"):
        st.rerun()

else:
    st.info("Selecteaza mai intai o companie")
# -------------------------
# INFO CLIENT
# -------------------------
st.info("""
**Context client actual:**  
Azure AD Hybrid • Microsoft 365 (SharePoint, OneDrive, Exchange) • Dynamics 365  
VPN • aplicatii web contracte • OT energie & gaz • ISO 27001 + NIS2
""")

# -------------------------
# TITLU + Start evaluare
# -------------------------
st.title("Evaluare de securitate cibernetica")

assessment_name = st.text_input("Nume evaluare / Referinta")

if "assessment_id" not in st.session_state:
    if st.button("Incepe evaluarea"):
        if company_id and assessment_name.strip():
            st.session_state.assessment_id = create_assessment(
                company_id,
                assessment_name.strip()
            )
            st.success("Evaluare inceputa!")
            st.rerun()
        else:
            st.warning("Selecteaza companie si completeaza numele evaluarii")

# -------------------------
# INTERFATA PRINCIPALA
# -------------------------
responses = []

if "assessment_id" in st.session_state:
    aid = st.session_state.assessment_id

    # Incarcam raspunsurile existente din baza de date
    existing_answers = get_answers_for_assessment(aid)
    loaded_responses = [
        {
            "domain": ans["domain"],
            "question": ans["question"],
            "score": ans["score"],
            "weight": 1,  # daca nu salvezi weight in db, lasi 1
            "notes": ans["notes"],
            "proof": ans["proof"]
        }
        for ans in existing_answers
    ]

    tab_names = [d["name"][lang] for d in data["domains"]]
    tabs = st.tabs(tab_names)

    for i, domain in enumerate(data["domains"]):
        with tabs[i]:
            st.header(domain["name"][lang])

            for q in domain["questions"]:
                st.subheader(q["text"][lang])

                st.caption(
                    f"Greutate: **{q.get('weight',1)}** | "
                    f"Risc: **{q.get('risk','Medium')}** | "
                    f"ISO: **{q.get('iso','N/A')}**"
                )

                score_label = st.selectbox(
                    "Evaluare",
                    ["Fail", "Partial", "Pass", "Not Applicable"],
                    key=f"score_{q['id']}"
                )

                score_map = {
                    "Fail": 0,
                    "Partial": 50,
                    "Pass": 100,
                    "Not Applicable": None
                }
                score = score_map[score_label]

                notes = st.text_area("Observatii / dovezi", key=f"notes_{q['id']}", height=80)

                proof = st.file_uploader(
                    "Incarca dovada (png/jpg)",
                    type=["png", "jpg", "jpeg"],
                    key=f"proof_{q['id']}"
                )

                responses.append({
                    "domain": domain["name"][lang],
                    "question": q["text"][lang],
                    "score": score,
                    "weight": q.get("weight", 1),
                    "notes": notes,
                    "proof": proof.name if proof else ""
                })

                if st.button(f"Salveaza raspuns {q['id']}", key=f"save_{q['id']}"):
                    if score is not None or notes or proof:
                        save_answer(
                            aid,
                            domain["name"][lang],
                            q["text"][lang],
                            score if score is not None else -1,
                            notes,
                            proof.name if proof else ""
                        )
                        st.success(f"Salvat {q['id']}")
                    else:
                        st.info("Nimic de salvat (doar N/A fara note/dovada)")

    # -------------------------
    # REZULTATE + GRAFIC + MATURITATE
    # -------------------------
    st.header("Rezultate")

    # combinam raspunsurile din baza + cele noi din sesiune
    all_responses = loaded_responses + responses
    scores = calculate_scores(all_responses)

    if scores:
        df = pd.DataFrame(
            [(d, s, get_maturity_level(s)) for d, s in scores.items()],
            columns=["Domeniu", "Scor ponderat", "Nivel maturitate"]
        )

        st.dataframe(df.style.format({"Scor ponderat": "{:.0f}"}), use_container_width=True)

        st.bar_chart(
            df.set_index("Domeniu")["Scor ponderat"],
            y="Scor ponderat",
            color="#2e7d32"
        )

        col1, col2 = st.columns([3,1])
        with col1:
            st.subheader("Recomandari automate")
            auto_reco = []

            for domain in data["domains"]:
                for q in domain["questions"]:
                    key = f"score_{q['id']}"
                    if key in st.session_state and st.session_state[key] == "Fail":
                        reco = q.get("recommendation", {}).get(lang, "Fara recomandare disponibila")
                        risk = q.get("risk", "Unknown")
                        iso = q.get("iso", "N/A")
                        auto_reco.append(f"[{risk}] ({iso}) - {reco}")

            st.text_area(
                "Recomandari generate automat (din Fail)",
                "\n".join(auto_reco) if auto_reco else "Nicio problema critica identificata",
                height=140
            )

        with col2:
            st.subheader("Scor general")
            avg = round(sum(scores.values()) / len(scores), 1) if scores else 0
            st.metric("Scor mediu ponderat", f"{avg}/100")

    # -------------------------
    # EXPORT - disponibil daca exista evaluare activa
    # -------------------------
    st.header("Export raport")

    final_reco = "\n".join(auto_reco) + "\n\n" + st.text_area(
        "Recomandari suplimentare / manuale",
        height=120,
        key="manual_reco_export"
    )

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        if st.button("Genereaza PDF"):
            pdf_buf = generate_pdf(scores, final_reco)
            st.download_button(
                label="Descarca PDF",
                data=pdf_buf,
                file_name=f"raport_{selected_company or 'firma'}_{assessment_name or 'evaluare'}.pdf",
                mime="application/pdf"
            )

    with col_exp2:
        if st.button("Genereaza Word"):
            word_buf = generate_word(
                scores,
                final_reco,
                selected_company or "Companie",
                assessment_name or "Evaluare"
            )
            st.download_button(
                label="Descarca Word",
                data=word_buf,
                file_name=f"raport_{selected_company or 'firma'}_{assessment_name or 'evaluare'}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

# -------------------------
# DASHBOARD EXECUTIV
# -------------------------
st.header("Dashboard executiv")

dashboard_data = get_assessment_scores()

if dashboard_data:
    df_dash = pd.DataFrame(
        dashboard_data,
        columns=["Evaluare", "Companie", "Scor mediu"]
    )
    st.dataframe(df_dash)
    st.bar_chart(df_dash.set_index("Evaluare")["Scor mediu"])
else:
    st.info("Nu exista inca evaluari salvate in baza de date.")
