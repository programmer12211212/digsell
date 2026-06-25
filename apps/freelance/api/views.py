from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.db.models import Q

from apps.freelance.models import FreelanceProject, Proposal, FreelancerProfile, Milestone
from apps.freelance.api.serializers import (
    ProjectSerializer,
    ProposalSerializer,
    ProfileSerializer,
    MilestoneSerializer,
)
from apps.freelance.services.workflow import submit_proposal, WorkflowError
from rest_framework.response import Response
from rest_framework import status


class FreelanceThrottle(UserRateThrottle):
    rate = "100/hour"


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FreelanceProject.objects.select_related("client", "category").prefetch_related("proposals")
    serializer_class = ProjectSerializer
    lookup_field = "slug"
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [FreelanceThrottle, AnonRateThrottle]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "budget", "deadline"]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        project_type = self.request.query_params.get("project_type")
        category = self.request.query_params.get("category")
        if status_param:
            qs = qs.filter(status=status_param)
        if project_type:
            qs = qs.filter(project_type=project_type)
        if category:
            qs = qs.filter(category_id=category)
        return qs


class ProposalViewSet(viewsets.ModelViewSet):
    serializer_class = ProposalSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [FreelanceThrottle]

    def get_queryset(self):
        user = self.request.user
        return Proposal.objects.filter(
            Q(freelancer=user) | Q(project__client=user)
        ).select_related("project", "freelancer")

    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            project = FreelanceProject.objects.get(pk=data.get("project"))
            proposal = submit_proposal(
                project,
                request.user,
                data.get("cover_letter", ""),
                data.get("bid_amount"),
                int(data.get("delivery_days", 7)),
                request,
            )
            return Response(ProposalSerializer(proposal).data, status=status.HTTP_201_CREATED)
        except (FreelanceProject.DoesNotExist, WorkflowError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FreelancerProfile.objects.select_related("user").prefetch_related("skills__skill", "portfolio")
    serializer_class = ProfileSerializer
    lookup_field = "user__username"
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [FreelanceThrottle, AnonRateThrottle]


class MilestoneViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [FreelanceThrottle]

    def get_queryset(self):
        user = self.request.user
        return Milestone.objects.filter(
            Q(project__client=user) | Q(project__assigned_freelancer=user)
        ).select_related("project")
