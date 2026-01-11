from django.test import TestCase
from django.urls import reverse
from .models import MealSignUp
from datetime import date

class MealsViewsTest(TestCase):
    def test_calendar_view(self):
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Missionary Meal Calendar")

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
        self.assertTrue(MealSignUp.objects.filter(date=d, name='John Doe').exists())
        self.assertContains(response, "John Doe")
        self.assertContains(response, "123-456-7890")
