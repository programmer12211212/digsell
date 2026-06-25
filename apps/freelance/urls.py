from django.urls import path, include

from . import views

app_name = "freelance"

urlpatterns = [
    path("", views.FreelanceProjectListView.as_view(), name="project_list"),
    path("create/", views.FreelanceProjectCreateView.as_view(), name="project_create"),
    path("order/<int:project_id>/", views.create_freelance_order, name="create_order"),
    path("project/<slug:slug>/", views.project_detail, name="project_detail"),
    path("dashboard/client/", views.client_dashboard, name="client_dashboard"),
    path("dashboard/freelancer/", views.freelancer_dashboard, name="freelancer_dashboard"),
    path("project/<int:project_id>/proposals/", views.manage_proposals, name="manage_proposals"),
    path("proposal/<int:proposal_id>/<str:action>/", views.proposal_action, name="proposal_action"),
    path("profile/<str:username>/", views.freelancer_profile, name="freelancer_profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("portfolio/add/", views.portfolio_add, name="portfolio_add"),
    path("project/<int:project_id>/milestones/", views.milestone_manage, name="milestone_manage"),
    path("milestone/<int:milestone_id>/complete/", views.milestone_complete, name="milestone_complete"),
    path("milestone/<int:milestone_id>/approve/", views.milestone_approve, name="milestone_approve"),
    path("pay/<int:milestone_id>/", views.escrow_payment, name="escrow_payment"),
    path("contract/<int:project_id>/", views.contract_view, name="contract_view"),
    path("project/<int:project_id>/chat/", views.project_chat, name="project_chat"),
    path("project/<int:project_id>/upload/", views.upload_project_file, name="upload_file"),
    path("project/<int:project_id>/cancel/", views.cancel_project_view, name="cancel_project"),
    path("project/<int:project_id>/review/", views.leave_review, name="leave_review"),
    path("project/<int:project_id>/dispute/", views.open_dispute, name="open_dispute"),
    path("ai/description/", views.ai_generate_description, name="ai_description"),
    path("search/", views.search_projects_htmx, name="search_htmx"),
    path("api/v1/", include("apps.freelance.api.urls")),
    
    # Contests (Tanlovlar)
    path("contests/", views.contest_list, name="contest_list"),
    path("contests/create/", views.contest_create, name="contest_create"),
    path("contests/<slug:slug>/", views.contest_detail, name="contest_detail"),
    path("contests/<int:contest_id>/pay/", views.contest_payment, name="contest_payment"),
    path("contests/<int:contest_id>/submit/", views.contest_submit, name="contest_submit"),
    path("contests/submission/<int:submission_id>/select/", views.contest_select_winner, name="contest_select_winner"),
    
    # Top Freelancers
    path("top-freelancers/", views.top_freelancers_list, name="top_freelancers"),
    
    # Verification
    path("profile/request-verification/", views.request_verification, name="request_verification"),
]
