from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.core.models import SchoolSetting


class AuthenticationRoleTests(TestCase):
    def setUp(self):
        self.client = Client()
        SchoolSetting.objects.create(school_name="Test School")
        self.admin = User.objects.create_user(username='admin_test', password='password123', role=User.Role.ADMIN)
        self.principal = User.objects.create_user(username='principal_test', password='password123', role=User.Role.PRINCIPAL)
        self.coordinator = User.objects.create_user(username='coordinator_test', password='password123', role=User.Role.COORDINATOR)
        self.teacher = User.objects.create_user(username='teacher_test', password='password123', role=User.Role.TEACHER)

    def test_login_page_renders(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In')

    def test_successful_login_redirects_to_dashboard(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin_test',
            'password': 'password123',
            'remember_me': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:dashboard'))

    def test_dashboard_access_for_authenticated_user(self):
        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Teacher Dashboard')

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(reverse('accounts:login') in response.url)

    def test_user_roles_properties(self):
        self.assertTrue(self.admin.is_admin)
        self.assertTrue(self.principal.is_principal)
        self.assertTrue(self.coordinator.is_coordinator)
        self.assertTrue(self.teacher.is_teacher)
