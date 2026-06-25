from django.contrib import admin

from apps.freelance.models import (
    FreelanceProject,
    Proposal,
    Milestone,
    Skill,
    FreelancerProfile,
    FreelancerSkill,
    PortfolioItem,
    FreelanceReview,
    PlatformCommission,
    FreelanceEscrowTransaction,
    FreelanceContract,
    FreelanceInvoice,
    FreelanceFile,
    FreelanceAuditLog,
    FreelanceDispute,
    Contest,
    ContestSubmission,
)


@admin.register(FreelanceProject)
class FreelanceProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "budget", "project_type", "status", "deadline", "created_at")
    list_filter = ("status", "project_type", "category", "is_featured")
    search_fields = ("title", "description", "slug")
    autocomplete_fields = ("client", "category", "assigned_freelancer")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-created_at",)


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ("project", "freelancer", "bid_amount", "status", "is_accepted", "is_flagged_spam")
    list_filter = ("status", "is_accepted", "is_flagged_spam")
    autocomplete_fields = ("project", "freelancer")


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "amount", "is_paid", "is_completed", "order_index")
    autocomplete_fields = ("project",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(FreelancerProfile)
class FreelancerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "hourly_rate", "is_top_rated", "completed_projects")
    list_filter = ("is_top_rated", "availability")
    search_fields = ("user__username", "title")


admin.site.register(FreelancerSkill)
admin.site.register(PortfolioItem)
admin.site.register(FreelanceReview)
admin.site.register(PlatformCommission)
admin.site.register(FreelanceContract)
admin.site.register(FreelanceInvoice)
admin.site.register(FreelanceFile)


@admin.register(FreelanceEscrowTransaction)
class FreelanceEscrowTransactionAdmin(admin.ModelAdmin):
    list_display = ("uuid", "project", "amount", "status", "provider", "created_at")
    list_filter = ("status", "provider")
    readonly_fields = ("uuid",)


@admin.register(FreelanceAuditLog)
class FreelanceAuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "model_name", "object_id", "user", "created_at")
    list_filter = ("action", "model_name")
    readonly_fields = ("created_at",)


@admin.register(FreelanceDispute)
class FreelanceDisputeAdmin(admin.ModelAdmin):
    list_display = ("project", "opened_by", "status", "created_at")
    list_filter = ("status",)


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "reward", "status", "deadline", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ContestSubmission)
class ContestSubmissionAdmin(admin.ModelAdmin):
    list_display = ("contest", "freelancer", "is_winner", "created_at")
    list_filter = ("is_winner",)
    search_fields = ("freelancer__username", "contest__title")

