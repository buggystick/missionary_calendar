from django.test import TestCase
from django.urls import reverse
from .models import MealSignUp
from datetime import date, timedelta
import calendar

class MealsViewsTest(TestCase):
    def test_calendar_view(self):
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Missionary Meal Calendar")
        # Should have "Next Month" link
        self.assertContains(response, "Next Month")
        # Should NOT have "Previous Month" link
        self.assertNotContains(response, "Previous Month")

    def test_calendar_next_month_view(self):
        today = date.today()
        current_month_first_day = today.replace(day=1)
        next_month_first_day = (current_month_first_day + timedelta(days=32)).replace(day=1)
        
        response = self.client.get(reverse('calendar') + f'?year={next_month_first_day.year}&month={next_month_first_day.month}')
        self.assertEqual(response.status_code, 200)
        # Should have "Previous Month" link (which actually goes back to current month)
        self.assertContains(response, "Previous Month")
        # Should NOT have "Next Month" link
        self.assertNotContains(response, "Next Month")

    def test_calendar_invalid_month_view(self):
        # Accessing a month that is not current or next should not show navigation links
        today = date.today()
        future_date = (today.replace(day=1) + timedelta(days=64)).replace(day=1)
        
        response = self.client.get(reverse('calendar') + f'?year={future_date.year}&month={future_date.month}')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Next Month")
        self.assertNotContains(response, "Previous Month")

    def test_signup_form_view(self):
        d = date(2026, 1, 15)
        response = self.client.get(reverse('meal_signup_form') + f'?date={d.isoformat()}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign up for January 15, 2026")

    def test_signup_submit(self):
        d = date(2026, 1, 15)
        response = self.client.post(reverse('meal_signup_submit') + f'?date={d.isoformat()}', {
            'name': 'John Doe',
            'phone': '123-456-7890'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(MealSignUp.objects.filter(date=d, name='John Doe', is_unavailable=False).exists())
        self.assertContains(response, "John Doe")
        self.assertContains(response, "123-456-7890")

    def test_signup_unavailable_submit(self):
        d = date(2026, 1, 16)
        response = self.client.post(reverse('meal_signup_submit') + f'?date={d.isoformat()}', {
            'is_unavailable': 'on'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(MealSignUp.objects.filter(date=d, is_unavailable=True).exists())
        self.assertContains(response, "Unavailable")
        self.assertNotContains(response, "Available")

    def test_signup_make_available_submit(self):
        d = date(2026, 1, 17)
        # First mark as unavailable
        MealSignUp.objects.create(date=d, is_unavailable=True)
        
        # Then make available by submitting without is_unavailable='on' and without details
        response = self.client.post(reverse('meal_signup_submit') + f'?date={d.isoformat()}', {
            'is_unavailable': '',
            'name': '',
            'phone': ''
        })
        self.assertEqual(response.status_code, 200)
        # Record should be deleted (or at least not unavailable and no name)
        self.assertFalse(MealSignUp.objects.filter(date=d).exists())
        self.assertNotContains(response, "Unavailable")
        self.assertNotContains(response, "Jane Doe")
