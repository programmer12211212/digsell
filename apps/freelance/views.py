from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, ListView
from django_ratelimit.decorators import ratelimit

from apps.marketplace.models import Category
from apps.payments.models import CompanyCard
from apps.freelance.forms import (
    EscrowPaymentForm,
    MilestoneForm,
    PortfolioForm,
    ProfileForm,
    ProjectForm,
    ProposalForm,
    ReviewForm,
    validate_upload_file,
    ContestForm,
    ContestSubmissionForm,
)
from apps.freelance.models import (
    FreelanceContract,
    FreelanceDispute,
    FreelanceEscrowTransaction,
    FreelanceFile,
    FreelanceProject,
    FreelanceReview,
    FreelancerProfile,
    FreelancerSkill,
    Milestone,
    PortfolioItem,
    Proposal,
    Skill,
    Contest,
    ContestSubmission,
)
from apps.freelance.permissions import user_can_bid, user_can_view_project
from apps.freelance.selectors.projects import (
    get_freelancer_profile,
    get_open_projects,
    get_project_by_slug,
    get_top_freelancers,
)
from apps.freelance.services.ai import ai_fraud_detection, ai_project_description, ai_proposal_generator
from apps.freelance.services.audit import log_audit
from apps.freelance.services.chat import start_project_chat
from apps.freelance.services.escrow import create_escrow_payment, release_escrow_to_freelancer
from apps.freelance.services.workflow import (
    WorkflowError,
    accept_proposal,
    approve_milestone,
    cancel_project,
    complete_milestone,
    reject_proposal,
    shortlist_proposal,
    submit_proposal,
)
from apps.freelance.utils import sanitize_text


class FreelanceProjectListView(ListView):
    template_name = "freelance/project_list.html"
    context_object_name = "projects"
    paginate_by = 12

    def get_queryset(self):
        return get_open_projects(self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()[:20]
        ctx["skills"] = Skill.objects.all()[:30]
        ctx["current_filters"] = self.request.GET
        return ctx


class FreelanceProjectCreateView(LoginRequiredMixin, CreateView):
    model = FreelanceProject
    form_class = ProjectForm
    template_name = "freelance/project_form.html"
    success_url = reverse_lazy("freelance:project_list")

    def form_valid(self, form):
        form.instance.client = self.request.user
        if not form.instance.deadline:
            form.instance.deadline = timezone.now() + timedelta(days=30)
        messages.success(self.request, "Loyiha e'lon qilindi.")
        log_audit(self.request.user, "project_created", "FreelanceProject", "new",
                  ip_address=self.request.META.get("REMOTE_ADDR"))
        return super().form_valid(form)


def project_detail(request, slug):
    project = get_project_by_slug(slug)
    if not project:
        return redirect("freelance:project_list")
    if not user_can_view_project(request.user, project):
        messages.error(request, "Bu loyihani ko'rish huquqingiz yo'q.")
        return redirect("freelance:project_list")
    FreelanceProject.objects.filter(pk=project.pk).update(view_count=project.view_count + 1)
    project.refresh_from_db()
    user_proposal = None
    if request.user.is_authenticated:
        user_proposal = project.proposals.filter(freelancer=request.user).first()
    
    # AI skill matching recommendations for client
    ai_recommendations_list = []
    if request.user.is_authenticated and request.user.id == project.client_id:
        from apps.freelance.services.ai import ai_skill_matching
        profiles = FreelancerProfile.objects.select_related("user").prefetch_related("skills__skill")
        scores = ai_skill_matching(project, profiles)
        recommended_profiles = []
        for p in profiles:
            score = scores.get(p.user_id, 0.0)
            recommended_profiles.append((p, score))
        recommended_profiles.sort(key=lambda x: x[1], reverse=True)
        # Only take profiles with some overlap or top ones if no requirements
        ai_recommendations_list = [
            {"profile": p[0], "score_percent": int(p[1] * 100)} 
            for p in recommended_profiles if p[1] > 0
        ][:5]

    return render(request, "freelance/project_detail.html", {
        "project": project,
        "user_proposal": user_proposal,
        "can_bid": user_can_bid(request.user, project),
        "ai_recommendations": ai_recommendations_list,
    })


@login_required
def client_dashboard(request):
    projects = FreelanceProject.objects.filter(client=request.user).prefetch_related("proposals")
    return render(request, "freelance/client_dashboard.html", {"projects": projects})


@login_required
def freelancer_dashboard(request):
    proposals = Proposal.objects.filter(freelancer=request.user).select_related("project")
    assigned = FreelanceProject.objects.filter(assigned_freelancer=request.user)
    profile, _ = FreelancerProfile.objects.get_or_create(user=request.user)
    
    # AI Recommended Projects
    from apps.freelance.services.ai import ai_recommendations
    ai_recs = ai_recommendations(request.user)
    rec_ids = [p['id'] for p in ai_recs]
    ai_projects = FreelanceProject.objects.filter(id__in=rec_ids).select_related("client", "category")

    return render(request, "freelance/freelancer_dashboard.html", {
        "proposals": proposals,
        "assigned_projects": assigned,
        "profile": profile,
        "ai_projects": ai_projects,
    })


@login_required
def manage_proposals(request, project_id):
    project = get_object_or_404(FreelanceProject, id=project_id, client=request.user)
    proposals = project.proposals.select_related("freelancer").order_by("-created_at")
    return render(request, "freelance/manage_proposals.html", {
        "project": project,
        "proposals": proposals,
    })


@login_required
@require_POST
def proposal_action(request, proposal_id, action):
    proposal = get_object_or_404(Proposal, id=proposal_id)
    try:
        if action == "accept":
            accept_proposal(proposal, request.user, request)
            messages.success(request, "Taklif qabul qilindi.")
        elif action == "reject":
            reject_proposal(proposal, request.user, request)
            messages.info(request, "Taklif rad etildi.")
        elif action == "shortlist":
            shortlist_proposal(proposal, request.user, request)
            messages.success(request, "Taklif shortlistga qo'shildi.")
        else:
            messages.error(request, "Noto'g'ri amal.")
    except WorkflowError as e:
        messages.error(request, str(e))
    return redirect("freelance:manage_proposals", project_id=proposal.project_id)


@login_required
@ratelimit(key="user", rate="5/h", method="POST", block=True)
def create_freelance_order(request, project_id):
    project = get_object_or_404(FreelanceProject, id=project_id, status=FreelanceProject.Status.OPEN)
    existing = Proposal.objects.filter(project=project, freelancer=request.user).first()
    if request.method == "POST":
        form = ProposalForm(request.POST)
        if form.is_valid():
            fraud = ai_fraud_detection(form.cleaned_data["cover_letter"])
            try:
                proposal = submit_proposal(
                    project,
                    request.user,
                    form.cleaned_data["cover_letter"],
                    form.cleaned_data["bid_amount"],
                    form.cleaned_data["delivery_days"],
                    request,
                )
                if fraud["is_suspicious"]:
                    proposal.is_flagged_spam = True
                    proposal.save(update_fields=["is_flagged_spam"])
                messages.success(request, "Taklifingiz yuborildi.")
                return redirect("freelance:project_detail", slug=project.slug)
            except WorkflowError as e:
                messages.error(request, str(e))
    else:
        form = ProposalForm()
        profile = FreelancerProfile.objects.filter(user=request.user).first()
        if profile and request.GET.get("ai") == "1":
            ai_text = ai_proposal_generator(project, profile)
            if ai_text:
                form.initial["cover_letter"] = ai_text
    return render(request, "freelance/proposal_form.html", {
        "project": project,
        "form": form,
        "existing": existing,
    })


@login_required
def profile_edit(request):
    from django.http import JsonResponse
    from decimal import Decimal
    import json
    
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Content-Type: {request.content_type}")
    print(f"DEBUG: META Content-Type: {request.META.get('CONTENT_TYPE')}")
    
    profile, _ = FreelancerProfile.objects.get_or_create(user=request.user)
    
    # Handle JSON POST request (from modal)
    is_json = 'application/json' in (request.content_type or '')
    print(f"DEBUG: is_json={is_json}")
    
    if request.method == "POST" and is_json:
        try:
            data = json.loads(request.body)
            print(f"DEBUG: JSON data received: {data}")
            
            profile.title = data.get('title', profile.title)
            profile.bio = data.get('bio', profile.bio)
            
            # Handle hourly_rate conversion
            hourly_rate = data.get('hourly_rate', profile.hourly_rate)
            if hourly_rate:
                profile.hourly_rate = Decimal(str(hourly_rate))
            
            # Handle experience_years conversion
            experience = data.get('experience_years', profile.experience_years)
            if experience:
                profile.experience_years = int(experience)
            
            profile.availability = data.get('availability', profile.availability)
            profile.phone = data.get('phone', profile.phone)
            profile.telegram = data.get('telegram', profile.telegram)
            profile.save()
            print(f"DEBUG: Profile saved successfully")
            return JsonResponse({'success': True, 'message': 'Profil yangilandi'})
        except Exception as e:
            import traceback
            print(f"DEBUG: Exception during save: {e}")
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    print(f"DEBUG: Falling through to form handling")
    # Handle form POST request (from profile_edit.html page)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil yangilandi.")
            return redirect("freelance:freelancer_profile", username=request.user.username)
    else:
        form = ProfileForm(instance=profile)
    
    portfolio = profile.portfolio.all()
    return render(request, "freelance/profile_edit.html", {"form": form, "portfolio": portfolio})


def freelancer_profile(request, username):
    profile = get_freelancer_profile(username)
    if not profile:
        messages.error(request, "Freelancer profili topilmadi.")
        return redirect("freelance:project_list")
    reviews = FreelanceReview.objects.filter(freelancer=profile.user).select_related("reviewer", "project")[:10]
    return render(request, "freelance/freelancer_profile.html", {
        "profile": profile,
        "reviews": reviews,
    })


@login_required
def portfolio_add(request):
    profile, _ = FreelancerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = PortfolioForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.profile = profile
            item.save()
            messages.success(request, "Portfolio qo'shildi.")
            return redirect("freelance:profile_edit")
    else:
        form = PortfolioForm()
    return render(request, "freelance/portfolio_form.html", {"form": form})


@login_required
def milestone_manage(request, project_id):
    project = get_object_or_404(FreelanceProject, id=project_id)
    if request.user.id not in (project.client_id, project.assigned_freelancer_id):
        messages.error(request, "Ruxsat yo'q.")
        return redirect("freelance:project_list")
    milestones = project.milestones.all()
    form = MilestoneForm()
    if request.method == "POST" and project.client_id == request.user.id:
        form = MilestoneForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.project = project
            m.save()
            messages.success(request, "Milestone qo'shildi.")
            return redirect("freelance:milestone_manage", project_id=project.id)
    return render(request, "freelance/milestone_manage.html", {
        "project": project,
        "milestones": milestones,
        "form": form,
    })


@login_required
@require_POST
def milestone_complete(request, milestone_id):
    milestone = get_object_or_404(Milestone, id=milestone_id)
    try:
        complete_milestone(milestone, request.user, request)
        messages.success(request, "Milestone tugallandi deb belgilandi.")
    except WorkflowError as e:
        messages.error(request, str(e))
    return redirect("freelance:milestone_manage", project_id=milestone.project_id)


@login_required
@require_POST
def milestone_approve(request, milestone_id):
    milestone = get_object_or_404(Milestone, id=milestone_id)
    try:
        approve_milestone(milestone, request.user, request)
        try:
            release_escrow_to_freelancer(milestone, request.user, request)
        except Exception:
            pass
        messages.success(request, "Milestone tasdiqlandi.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("freelance:milestone_manage", project_id=milestone.project_id)


@login_required
def escrow_payment(request, milestone_id):
    milestone = get_object_or_404(Milestone, id=milestone_id)
    project = milestone.project
    if project.client_id != request.user.id:
        messages.error(request, "Faqat mijoz to'lov qila oladi.")
        return redirect("freelance:project_list")
    cards = CompanyCard.objects.filter(is_active=True)
    if request.method == "POST":
        form = EscrowPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            create_escrow_payment(
                project,
                milestone,
                request.user,
                milestone.amount,
                form.cleaned_data["payment_method"],
                screenshot=form.cleaned_data["screenshot"],
            )
            messages.success(request, "To'lov yuborildi. Admin tasdiqlashini kuting.")
            return redirect("freelance:client_dashboard")
    else:
        form = EscrowPaymentForm()
    return render(request, "freelance/escrow_payment.html", {
        "milestone": milestone,
        "project": project,
        "form": form,
        "company_cards": cards,
    })


@login_required
def contract_view(request, project_id):
    project = get_object_or_404(FreelanceProject, id=project_id)
    if request.user.id not in (project.client_id, project.assigned_freelancer_id):
        messages.error(request, "Ruxsat yo'q.")
        return redirect("freelance:project_list")
    contract = FreelanceContract.objects.filter(project=project).first()
    return render(request, "freelance/contract_view.html", {"project": project, "contract": contract})


@login_required
def project_chat(request, project_id):
    project = get_object_or_404(FreelanceProject, id=project_id)
    conv = start_project_chat(project, request.user)
    if not conv:
        messages.error(request, "Chat mavjud emas.")
        return redirect("freelance:project_detail", slug=project.slug)
    return redirect("chat:chat_detail", conversation_id=conv.id)


@login_required
@require_POST
def upload_project_file(request, project_id):
    project = get_object_or_404(FreelanceProject, id=project_id)
    if request.user.id not in (project.client_id, project.assigned_freelancer_id):
        return JsonResponse({"error": "Ruxsat yo'q"}, status=403)
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "Fayl tanlanmagan"}, status=400)
    try:
        validate_upload_file(f)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    FreelanceFile.objects.create(
        project=project,
        uploaded_by=request.user,
        file=f,
        original_name=f.name,
        file_size=f.size,
        mime_type=f.content_type or "",
    )
    messages.success(request, "Fayl yuklandi.")
    return redirect("freelance:project_detail", slug=project.slug)


@login_required
@require_POST
def cancel_project_view(request, project_id):
    project = get_object_or_404(FreelanceProject, id=project_id)
    try:
        cancel_project(project, request.user, request)
        messages.success(request, "Loyiha bekor qilindi.")
    except WorkflowError as e:
        messages.error(request, str(e))
    return redirect("freelance:client_dashboard")


@login_required
def leave_review(request, project_id):
    project = get_object_or_404(
        FreelanceProject, id=project_id, status=FreelanceProject.Status.COMPLETED, client=request.user
    )
    if not project.assigned_freelancer:
        return redirect("freelance:client_dashboard")
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            FreelanceReview.objects.create(
                project=project,
                reviewer=request.user,
                freelancer=project.assigned_freelancer,
                rating=form.cleaned_data["rating"],
                comment=sanitize_text(form.cleaned_data["comment"]),
            )
            profile = FreelancerProfile.objects.filter(user=project.assigned_freelancer).first()
            if profile:
                profile.completed_projects += 1
                profile.save(update_fields=["completed_projects"])
            messages.success(request, "Sharh qoldirildi.")
            return redirect("freelance:client_dashboard")
    else:
        form = ReviewForm()
    return render(request, "freelance/review_form.html", {"project": project, "form": form})


@login_required
@require_POST
def open_dispute(request, project_id):
    project = get_object_or_404(FreelanceProject, id=project_id)
    if request.user.id not in (project.client_id, project.assigned_freelancer_id):
        messages.error(request, "Ruxsat yo'q.")
        return redirect("freelance:project_list")
    reason = sanitize_text(request.POST.get("reason", ""))
    if reason:
        FreelanceDispute.objects.create(project=project, opened_by=request.user, reason=reason)
        project.status = FreelanceProject.Status.DISPUTED
        project.save(update_fields=["status"])
        messages.success(request, "Nizo ochildi.")
    return redirect("freelance:project_detail", slug=project.slug)


@login_required
@require_GET
def ai_generate_description(request):
    title = request.GET.get("title", "")
    category = request.GET.get("category", "")
    budget = request.GET.get("budget", "")
    if not title:
        return JsonResponse({"description": ""})
    desc = ai_project_description(title, category, budget)
    return JsonResponse({"description": desc})


@require_GET
def search_projects_htmx(request):
    projects = get_open_projects(request.GET)[:12]
    return render(request, "freelance/partials/project_cards.html", {"projects": projects})


# ==========================================
# CONTESTS, TOP FREELANCERS & VERIFICATION
# ==========================================

def contest_list(request):
    contests = Contest.objects.all().select_related("client", "category")
    categories = Category.objects.all()[:20]
    return render(request, "freelance/contest_list.html", {
        "contests": contests,
        "categories": categories,
    })


def contest_detail(request, slug):
    contest = get_object_or_404(Contest.objects.select_related("client", "category"), slug=slug)
    submissions = contest.submissions.select_related("freelancer").all()
    
    user_submission = None
    if request.user.is_authenticated:
        user_submission = contest.submissions.filter(freelancer=request.user).first()
        
    form = ContestSubmissionForm()
    return render(request, "freelance/contest_detail.html", {
        "contest": contest,
        "submissions": submissions,
        "user_submission": user_submission,
        "form": form,
    })


@login_required
def contest_create(request):
    if request.method == "POST":
        form = ContestForm(request.POST)
        if form.is_valid():
            contest = form.save(commit=False)
            contest.client = request.user
            contest.save()
            
            # Create a dummy project to link the escrow transaction
            dummy_project = FreelanceProject.objects.create(
                client=request.user,
                title=f"Contest: {contest.title}",
                description=contest.description,
                budget=contest.reward,
                deadline=contest.deadline,
                status=FreelanceProject.Status.OPEN,
            )
            messages.success(request, "Tanlov yaratildi! Mukofot jamg'armasini Escrow orqali to'lang.")
            return redirect("freelance:contest_payment", contest_id=contest.id)
    else:
        form = ContestForm()
    return render(request, "freelance/contest_form.html", {"form": form})


@login_required
def contest_payment(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id, client=request.user)
    cards = CompanyCard.objects.filter(is_active=True)
    project = FreelanceProject.objects.filter(client=request.user, title=f"Contest: {contest.title}").first()
    
    if request.method == "POST":
        form = EscrowPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            from apps.freelance.services.commission import calculate_commission
            from decimal import Decimal
            commission, _ = calculate_commission(Decimal(str(contest.reward)))
            
            tx = FreelanceEscrowTransaction.objects.create(
                project=project,
                payer=request.user,
                amount=contest.reward,
                commission_amount=commission,
                payment_method=form.cleaned_data["payment_method"],
                screenshot=form.cleaned_data["screenshot"],
                status=FreelanceEscrowTransaction.Status.PENDING,
            )
            contest.escrow_transaction = tx
            contest.status = Contest.Status.OPEN
            contest.save()
            messages.success(request, "To'lov yuborildi. Tanlov faollashtirildi!")
            return redirect("freelance:contest_list")
    else:
        form = EscrowPaymentForm()
        
    return render(request, "freelance/escrow_payment.html", {
        "project": project,
        "form": form,
        "company_cards": cards,
        "contest": contest,
    })


@login_required
@require_POST
def contest_submit(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id, status=Contest.Status.OPEN)
    if contest.client == request.user:
        messages.error(request, "O'z tanlovingizga ish yubora olmaysiz.")
        return redirect("freelance:contest_detail", slug=contest.slug)
        
    form = ContestSubmissionForm(request.POST, request.FILES)
    if form.is_valid():
        submission, created = ContestSubmission.objects.update_or_create(
            contest=contest,
            freelancer=request.user,
            defaults={
                "description": form.cleaned_data["description"],
                "file": form.cleaned_data["file"]
            }
        )
        messages.success(request, "Ishingiz muvaffaqiyatli topshirildi!")
    else:
        messages.error(request, "Xatolik yuz berdi. Iltimos, fayl turi va hajmini tekshiring.")
        
    return redirect("freelance:contest_detail", slug=contest.slug)


@login_required
@require_POST
def contest_select_winner(request, submission_id):
    submission = get_object_or_404(ContestSubmission.objects.select_related("contest"), id=submission_id)
    contest = submission.contest
    if contest.client != request.user:
        messages.error(request, "Faqat tanlov egasi g'olibni tanlay oladi.")
        return redirect("freelance:contest_detail", slug=contest.slug)
        
    if contest.status == Contest.Status.COMPLETED:
        messages.error(request, "Ushbu tanlov allaqachon yakunlangan.")
        return redirect("freelance:contest_detail", slug=contest.slug)
        
    contest.winner = submission
    contest.status = Contest.Status.COMPLETED
    contest.save()
    
    submission.is_winner = True
    submission.save()
    
    from apps.payments.models import EscrowAccount
    from apps.freelance.services.commission import calculate_commission
    
    tx = contest.escrow_transaction
    if tx:
        payee = submission.freelancer
        commission, net = calculate_commission(tx.amount)
        
        payer_escrow, _ = EscrowAccount.objects.get_or_create(user=tx.payer)
        payee_escrow, _ = EscrowAccount.objects.get_or_create(user=payee)
        
        if payer_escrow.frozen_balance >= tx.amount:
            payer_escrow.frozen_balance -= tx.amount
        payer_escrow.save()
        
        payee_escrow.balance += net
        payee_escrow.save()
        
        payee.total_earned = (payee.total_earned or 0) + net
        payee.save(update_fields=["total_earned"])
        
        tx.status = FreelanceEscrowTransaction.Status.RELEASED
        tx.payee = payee
        tx.commission_amount = commission
        tx.save()
        
        messages.success(request, f"G'olib tanlandi! Mukofot jamg'armasi ({net} UZS) freelancerga o'tkazildi.")
    else:
        messages.success(request, "G'olib tanlandi! (Escrow to'lovi topilmadi)")
        
    return redirect("freelance:contest_detail", slug=contest.slug)


def top_freelancers_list(request):
    freelancers = get_top_freelancers(limit=20)
    return render(request, "freelance/top_freelancers.html", {
        "freelancers": freelancers
    })


@login_required
def request_verification(request):
    profile, _ = FreelancerProfile.objects.get_or_create(user=request.user)
    profile.verified_at = timezone.now()
    profile.save()
    messages.success(request, "Tabriklaymiz! Sizning profilingiz muvaffaqiyatli verifikatsiya qilindi (tasdiqlandi).")
    return redirect("freelance:freelancer_dashboard")

