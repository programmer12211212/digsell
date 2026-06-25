from rest_framework import serializers

from apps.freelance.models import (
    FreelanceProject,
    Proposal,
    FreelancerProfile,
    Milestone,
    Skill,
    FreelanceReview,
)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "slug"]


class ProjectSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(source="client.username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, allow_null=True)
    proposals_count = serializers.SerializerMethodField()

    class Meta:
        model = FreelanceProject
        fields = [
            "id", "slug", "title", "description", "project_type", "budget",
            "hourly_rate", "estimated_hours", "deadline", "status",
            "client_username", "category_name", "progress_percent",
            "is_featured", "view_count", "proposals_count", "created_at",
        ]
        read_only_fields = ["slug", "status", "view_count", "progress_percent"]

    def get_proposals_count(self, obj):
        return obj.proposals.count()


class ProposalSerializer(serializers.ModelSerializer):
    freelancer_username = serializers.CharField(source="freelancer.username", read_only=True)
    project_title = serializers.CharField(source="project.title", read_only=True)

    class Meta:
        model = Proposal
        fields = [
            "id", "project", "project_title", "freelancer", "freelancer_username",
            "cover_letter", "bid_amount", "delivery_days", "status",
            "ai_match_score", "created_at",
        ]
        read_only_fields = ["freelancer", "status", "ai_match_score"]


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    rating = serializers.DecimalField(source="user.rating", max_digits=3, decimal_places=2, read_only=True)
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = FreelancerProfile
        fields = [
            "id", "username", "title", "bio", "hourly_rate", "experience_years",
            "availability", "is_top_rated", "is_verified", "completed_projects",
            "total_earnings",
        ]


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = [
            "id", "project", "title", "description", "amount", "order_index",
            "due_date", "is_paid", "is_completed", "approved_at",
        ]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreelanceReview
        fields = ["id", "project", "reviewer", "freelancer", "rating", "comment", "created_at"]
        read_only_fields = ["reviewer"]
