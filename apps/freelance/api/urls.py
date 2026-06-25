from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.freelance.api.views import (
    ProjectViewSet,
    ProposalViewSet,
    ProfileViewSet,
    MilestoneViewSet,
)

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="api-projects")
router.register("proposals", ProposalViewSet, basename="api-proposals")
router.register("profiles", ProfileViewSet, basename="api-profiles")
router.register("milestones", MilestoneViewSet, basename="api-milestones")

urlpatterns = [
    path("", include(router.urls)),
]
