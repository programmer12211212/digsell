from apps.chat.models import Conversation
from apps.freelance.models import FreelancerProfile


def get_or_create_project_conversation(project):
    conv = Conversation.objects.filter(freelance_project=project).first()
    if conv:
        return conv
    conv = Conversation.objects.create(freelance_project=project)
    conv.participants.add(project.client)
    if project.assigned_freelancer:
        conv.participants.add(project.assigned_freelancer)
    return conv


def start_project_chat(project, user):
    if user.id not in (project.client_id, project.assigned_freelancer_id):
        return None
    return get_or_create_project_conversation(project)


def update_top_rated_status(profile: FreelancerProfile):
    new_status = (
        profile.completed_projects >= 10
        and float(profile.user.rating or 0) >= 4.8
    )
    if profile.is_top_rated != new_status:
        profile.is_top_rated = new_status
        profile.save(update_fields=["is_top_rated"])
