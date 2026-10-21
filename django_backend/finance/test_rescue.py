"""Submission-critical authorization regression tests.

Run: python manage.py test finance.test_rescue
"""
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Branch, Role, User


class RescueAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = Branch.objects.create(
            branch_name="Rescue branch", city="Kochi",
            state="Kerala", ifsc_code="RESC000001", phone="9000000001"
        )
        cls.other_branch = Branch.objects.create(
            branch_name="Other rescue branch", city="Kannur",
            state="Kerala", ifsc_code="RESC000002", phone="9000000002"
        )
        for name in ("Admin", "Manager", "Analyst", "Customer"):
            Role.objects.get_or_create(role_name=name)
        for role in ("Admin", "Manager", "Analyst", "Customer"):
            User.objects.create_user(
                username=role.lower(), password="StrongPassword123!",
                email=f"{role.lower()}@example.org",
                role=Role.objects.get(role_name=role),
                branch=cls.branch,
            )

    def as_role(self, role):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(username=role.lower()))
        return client

    def test_admin_creates_usable_hashed_password(self):
        response = self.as_role("Admin").post("/api/users/", {
            "username": "newcustomer", "email": "newcustomer@example.org",
            "password": "AnotherStrongPass123!",
            "role": Role.objects.get(role_name="Customer").pk,
            "branch": self.branch.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        created = User.objects.get(username="newcustomer")
        self.assertTrue(created.check_password("AnotherStrongPass123!"))
        self.assertNotIn("password", response.data)

    def test_manager_creates_customer_only_in_own_branch(self):
        response = self.as_role("Manager").post("/api/users/", {
            "username": "managercreated",
            "email": "managercreated@example.org",
            "password": "AnotherStrongPass123!",
            "role": Role.objects.get(role_name="Admin").pk,
            "branch": self.other_branch.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        created = User.objects.get(username="managercreated")
        self.assertEqual(created.role.role_name, "Customer")
        self.assertEqual(created.branch, self.branch)
        self.assertTrue(created.check_password("AnotherStrongPass123!"))

    def test_analyst_cannot_mutate_analytical_results(self):
        client = self.as_role("Analyst")
        self.assertEqual(
            client.post("/api/fraud-predictions/", {}, format="json").status_code, 405
        )
        self.assertEqual(
            client.post("/api/forecasts/", {}, format="json").status_code, 405
        )

    def test_manager_cannot_view_global_analytics(self):
        client = self.as_role("Manager")
        for endpoint in ("/api/dashboard/", "/api/report/", "/api/forecasts/"):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(client.get(endpoint).status_code, 403)

    def test_analyst_can_view_dashboard(self):
        with patch("finance.views.get_dashboard_data", return_value={"summary": {}}):
            response = self.as_role("Analyst").get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
