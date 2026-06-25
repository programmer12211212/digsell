import json

from apps.ai_system.services import _call_groq


def ai_project_description(title, category="", budget=""):
    messages = [
        {
            "role": "system",
            "content": (
                "Sen professional freelance loyiha tavsifi yozuvchisisan. "
                "O'zbek tilida aniq, professional loyiha tavsifi yoz. "
                "JSON format: {\"description\": \"...\"}"
            ),
        },
        {
            "role": "user",
            "content": f"Sarlavha: {title}\nKategoriya: {category}\nBudjet: {budget} UZS",
        },
    ]
    result = _call_groq(messages, max_tokens=800, temperature=0.5)
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean).get("description", result)
        except (json.JSONDecodeError, IndexError):
            return result
    return ""


def ai_proposal_generator(project, profile):
    messages = [
        {
            "role": "system",
            "content": "Sen professional freelancer. Qisqa, ishonchli taklif xati yoz. O'zbek tilida.",
        },
        {
            "role": "user",
            "content": (
                f"Loyiha: {project.title}\n"
                f"Tavsif: {project.description[:500]}\n"
                f"Freelancer: {profile.title if profile else ''}\n"
                f"Bio: {profile.bio[:300] if profile else ''}"
            ),
        },
    ]
    return _call_groq(messages, max_tokens=600, temperature=0.6) or ""


def ai_skill_matching(project, freelancers):
    scores = {}
    required = set(project.skills_required.values_list("name", flat=True))
    for profile in freelancers:
        user_skills = set(profile.skills.select_related("skill").values_list("skill__name", flat=True))
        if not required:
            scores[profile.user_id] = 0.5
        else:
            overlap = len(required & user_skills) / len(required)
            scores[profile.user_id] = round(overlap, 2)
    return scores


def ai_fraud_detection(text, user_history_count=0):
    suspicious = []
    if len(text) < 20:
        suspicious.append("short_text")
    if user_history_count > 20:
        suspicious.append("high_volume")
    spam_words = ["telegram", "whatsapp", "t.me", "click here"]
    lower = text.lower()
    for word in spam_words:
        if word in lower:
            suspicious.append(f"spam_word:{word}")
    return {"is_suspicious": len(suspicious) > 0, "flags": suspicious}


def ai_recommendations(user):
    from apps.freelance.selectors.projects import get_open_projects

    projects = get_open_projects()[:5]
    return [{"id": p.id, "title": p.title, "budget": str(p.budget)} for p in projects]
