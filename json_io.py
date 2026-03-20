from db import (
    create_assessment,
    upsert_answer,
    save_executive_summary,
    add_recommendation,
)


def export_assessment_package(
    company_name,
    assessment_name,
    assessment_date,
    language,
    scores,
    summary,
    answers,
    recommendations,
    mapping_rows,
    include_proof=False,
    include_mapping=False,
    export_mode="Executive",
    management_content=None,
):
    return {
        "company_name": company_name,
        "assessment_name": assessment_name,
        "assessment_date": assessment_date,
        "language": language,
        "export_mode": export_mode,
        "include_proof": include_proof,
        "include_mapping": include_mapping,
        "scores": scores,
        "summary": summary,
        "answers": answers,
        "recommendations": recommendations,
        "mapping_rows": mapping_rows,
        "management_content": management_content or {},
    }


def import_assessment_package(payload, company_id, user_id, assessment_name):
    new_aid = create_assessment(company_id=company_id, user_id=user_id, name=assessment_name)

    for ans in payload.get("answers", []):
        upsert_answer(
            assessment_id=new_aid,
            domain_id=ans.get("domain_id", ""),
            domain_name=ans.get("domain", ""),
            question_id=ans.get("question_id", ""),
            question_text=ans.get("question", ""),
            answer_value=ans.get("answer_value", ""),
            score=ans.get("score"),
            notes=ans.get("notes", ""),
            proof=ans.get("proof", ""),
        )

    save_executive_summary(new_aid, payload.get("summary", ""))

    for reco in payload.get("recommendations", []):
        add_recommendation(
            assessment_id=new_aid,
            domain_id=reco.get("domain_id", ""),
            domain_name=reco.get("domain_name", ""),
            text=reco.get("text", ""),
            risk=reco.get("risk", "Medium"),
            source=reco.get("source", "manual"),
            recommendation_key=reco.get("recommendation_key", ""),
            responsible=reco.get("responsible", "") or "",
            deadline=reco.get("deadline"),
            status=reco.get("status", "Open"),
        )

    return new_aid
