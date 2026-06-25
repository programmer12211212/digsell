from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.users.models import User
from apps.freelance.models import FreelanceProject, Proposal, FreelancerProfile
from apps.freelance.services.workflow import submit_proposal, WorkflowError
from apps.freelance.services.commission import calculate_commission
from apps.freelance.utils import sanitize_text


class FreelanceRegressionTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user("client", "c@test.com", "pass12345")
        self.freelancer = User.objects.create_user("freelancer", "f@test.com", "pass12345")
        self.project = FreelanceProject.objects.create(
            client=self.client_user,
            title="Test Project",
            description="Desc",
            budget=Decimal("1000000"),
            deadline=timezone.now() + timedelta(days=30),
        )

    def test_project_list_url(self):
        r = self.client.get(reverse("freelance:project_list"))
        self.assertEqual(r.status_code, 200)

    def test_create_order_get_renders(self):
        self.client.login(username="freelancer", password="pass12345")
        r = self.client.get(reverse("freelance:create_order", args=[self.project.id]))
        self.assertEqual(r.status_code, 200)

    def test_self_bid_blocked(self):
        with self.assertRaises(WorkflowError):
            submit_proposal(self.project, self.client_user, "letter", Decimal("500000"), 7)

    def test_duplicate_bid_blocked(self):
        submit_proposal(self.project, self.freelancer, "letter", Decimal("500000"), 7)
        with self.assertRaises(WorkflowError):
            submit_proposal(self.project, self.freelancer, "letter2", Decimal("600000"), 5)

    def test_backward_compat_create_order_post(self):
        self.client.login(username="freelancer", password="pass12345")
        r = self.client.post(reverse("freelance:create_order", args=[self.project.id]), {
            "bid_amount": "800000",
            "cover_letter": "I can do this",
            "delivery_days": "10",
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Proposal.objects.filter(project=self.project).count(), 1)


class FreelanceSecurityTests(TestCase):
    def test_xss_sanitize(self):
        dirty = "<script>alert(1)</script>Hello"
        self.assertEqual(sanitize_text(dirty), "Hello")

    def test_commission_calculation(self):
        commission, net = calculate_commission(Decimal("1000000"))
        self.assertGreater(commission, 0)
        self.assertEqual(commission + net, Decimal("1000000"))


class FreelanceIntegrationTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user("client2", "c2@test.com", "pass12345")
        self.freelancer = User.objects.create_user("freelancer2", "f2@test.com", "pass12345")
        FreelancerProfile.objects.create(user=self.freelancer, title="Dev")
        self.project = FreelanceProject.objects.create(
            client=self.client_user,
            title="Integration Project",
            description="Long description",
            budget=Decimal("2000000"),
            deadline=timezone.now() + timedelta(days=14),
        )

    def test_project_detail_by_slug(self):
        r = self.client.get(reverse("freelance:project_detail", args=[self.project.slug]))
        self.assertEqual(r.status_code, 200)

    def test_api_projects_list(self):
        r = self.client.get("/freelance/api/v1/projects/")
        self.assertEqual(r.status_code, 200)
