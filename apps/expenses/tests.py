from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from decimal import Decimal

from apps.accounts.models import User
from apps.expenses.models import ExpenseCategory, Expense


class ExpenseManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin_exp_test',
            password='password123',
            email='admin_exp@school.test',
            role=User.Role.ADMIN
        )
        self.client.force_login(self.admin_user)

        self.category = ExpenseCategory.objects.create(
            name='Electricity Charges',
            code='ELE',
            description='Power bills'
        )

        self.expense = Expense.objects.create(
            expense_number='EXP-2026-00099',
            category=self.category,
            title='Campus 1 Electricity Bill',
            amount=Decimal('45000.00'),
            expense_date=date(2026, 9, 10),
            payment_method=Expense.PaymentMethod.ONLINE,
            payee_name='IESCO Power',
            recorded_by=self.admin_user,
            status=Expense.Status.PAID
        )

    def test_expense_list_view(self):
        response = self.client.get(reverse('expenses:expense_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EXP-2026-00099')
        self.assertContains(response, 'Campus 1 Electricity Bill')

    def test_financial_summary_view(self):
        response = self.client.get(reverse('expenses:financial_summary'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Financial Summary')
        self.assertContains(response, 'Electricity Charges')

    def test_expense_create_view(self):
        response = self.client.post(reverse('expenses:expense_create'), {
            'category': self.category.id,
            'title': 'Office Stationery and Markers',
            'amount': '5000.00',
            'expense_date': '2026-09-15',
            'payment_method': 'CASH',
            'payee_name': 'Stationery Mart',
            'status': 'PAID',
            'remarks': 'Class markers and dusters'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(title='Office Stationery and Markers').exists())
