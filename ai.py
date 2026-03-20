import os


def _fallback_summary(company_name, assessment_name, overall_score, domain_scores, lang="en"):
    if not domain_scores:
        return (
            "No sufficient assessment data is available yet."
            if lang == "en"
            else "Nu exista suficiente date de evaluare momentan."
        )

    weakest = sorted(domain_scores.items(), key=lambda x: x[1])[:3]
    strongest = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:3]

    if lang == "ro":
        weak_text = ", ".join([f"{d} ({s:.0f})" for d, s in weakest])
        strong_text = ", ".join([f"{d} ({s:.0f})" for d, s in strongest])
        return (
            f"Evaluarea '{assessment_name}' pentru compania '{company_name}' indica un scor general de "
            f"{overall_score:.1f}/100. Domeniile cele mai slabe sunt: {weak_text}. "
            f"Domeniile cele mai mature sunt: {strong_text}. "
            f"Se recomanda prioritizarea masurilor pentru domeniile cu scor scazut, cu responsabili si termene clare."
        )

    weak_text = ", ".join([f"{d} ({s:.0f})" for d, s in weakest])
    strong_text = ", ".join([f"{d} ({s:.0f})" for d, s in strongest])
    return (
        f"The assessment '{assessment_name}' for company '{company_name}' shows an overall score of "
        f"{overall_score:.1f}/100. The weakest domains are: {weak_text}. "
        f"The strongest domains are: {strong_text}. "
        f"Priority should be given to remediation plans for low-scoring domains, with clear owners and deadlines."
    )


def generate_executive_summary(company_name, assessment_name, overall_score, domain_scores, lang="en"):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_summary(company_name, assessment_name, overall_score, domain_scores, lang)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        score_lines = "\n".join([f"- {k}: {v:.1f}/100" for k, v in domain_scores.items()])

        if lang == "ro":
            prompt = f"""
Genereaza un executive summary profesionist, concis, in limba romana, fara diacritice.
Companie: {company_name}
Evaluare: {assessment_name}
Scor general: {overall_score:.1f}/100

Scoruri pe domenii:
{score_lines}

Creeaza 2-3 paragrafe executive, orientate spre management, cu ton profesionist.
"""
        else:
            prompt = f"""
Generate a concise professional executive summary in English.
Company: {company_name}
Assessment: {assessment_name}
Overall score: {overall_score:.1f}/100

Domain scores:
{score_lines}

Write 2-3 management-oriented paragraphs with a professional tone.
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )

        text = getattr(response, "output_text", None)
        if text:
            return text.strip()

        return _fallback_summary(company_name, assessment_name, overall_score, domain_scores, lang)
    except Exception:
        return _fallback_summary(company_name, assessment_name, overall_score, domain_scores, lang)
