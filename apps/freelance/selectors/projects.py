from django.core.cache import cache
from django.db.models import Q, Avg, Count

from apps.freelance.models import FreelanceProject, FreelancerProfile, Skill


def get_open_projects(filters=None):
    filters = filters or {}
    qs = FreelanceProject.objects.filter(
        status=FreelanceProject.Status.OPEN
    ).select_related("client", "category").prefetch_related("skills_required", "proposals")

    q = filters.get("q")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    budget = filters.get("budget")
    if budget == "low":
        qs = qs.filter(budget__lte=500000)
    elif budget == "mid":
        qs = qs.filter(budget__gt=500000, budget__lte=2000000)
    elif budget == "high":
        qs = qs.filter(budget__gt=2000000)

    category = filters.get("category")
    if category:
        qs = qs.filter(category_id=category)

    project_type = filters.get("project_type")
    if project_type:
        qs = qs.filter(project_type=project_type)

    skill = filters.get("skill")
    if skill:
        qs = qs.filter(skills_required__id=skill)

    min_rating = filters.get("min_rating")
    if min_rating:
        qs = qs.filter(client__rating__gte=min_rating)

    sort = filters.get("sort", "newest")
    sort_map = {
        "newest": "-created_at",
        "budget_asc": "budget",
        "budget_desc": "-budget",
        "deadline": "deadline",
    }
    return qs.order_by(sort_map.get(sort, "-created_at")).distinct()


def get_top_freelancers(limit=10):
    cache_key = "freelance:top_freelancers"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    qs = (
        FreelancerProfile.objects.filter(is_top_rated=True)
        .select_related("user")
        .prefetch_related("skills__skill")[:limit]
    )
    result = list(qs)
    cache.set(cache_key, result, 300)
    return result


def get_freelancer_profile(username):
    return (
        FreelancerProfile.objects.select_related("user")
        .prefetch_related("portfolio", "skills__skill")
        .filter(user__username=username)
        .first()
    )


def get_project_by_slug(slug):
    return (
        FreelanceProject.objects.select_related("client", "category", "assigned_freelancer")
        .prefetch_related("proposals__freelancer", "milestones", "skills_required")
        .filter(slug=slug)
        .first()
    )
