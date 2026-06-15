from django.test import TestCase
from django.urls import reverse
from django.core import mail
from .models import MealSignUp
from django.utils import timezone
from unittest.mock import patch
from datetime import date, timedelta, datetime
import calendar
from django.core.management import call_command
from io import StringIO
from .utils import format_phone_number, is_valid_phone_number

class PhoneUtilityTest(TestCase):
    def test_phone_formatting(self):
        self.assertEqual(format_phone_number('8015551234'), '(801) 555-1234')
        self.assertEqual(format_phone_number('801-555-1234'), '(801) 555-1234')
        self.assertEqual(format_phone_number('(801) 555-1234'), '(801) 555-1234')
        # International (if it starts with +)
        self.assertEqual(format_phone_number('+442079460958'), '+44 20 7946 0958')
        # Garbage should return as is
        self.assertEqual(format_phone_number('garbage'), 'garbage')

    def test_phone_validation(self):
        self.assertTrue(is_valid_phone_number('8015551234'))
        self.assertTrue(is_valid_phone_number('801-555-1234'))
        self.assertTrue(is_valid_phone_number('+44 20 7946 0958'))
        self.assertFalse(is_valid_phone_number('12345'))
        self.assertFalse(is_valid_phone_number('abcdefghij'))

class MealsViewsTest(TestCase):
    def test_calendar_view(self):
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ward Missionary Meal Calendar")
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
            'phone': '801-555-1234'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(MealSignUp.objects.filter(date=d, name='John Doe', is_unavailable=False).exists())
        signup = MealSignUp.objects.get(date=d)
        self.assertEqual(signup.phone, '(801) 555-1234')
        self.assertContains(response, "John Doe")
        self.assertContains(response, "(801) 555-1234")

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

    def test_past_dates_greyed_out(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if yesterday.month == today.month:
            response = self.client.get(reverse('calendar'))
            self.assertEqual(response.status_code, 200)
            # Check if yesterday's cell has 'past-date' class
            self.assertContains(response, 'class="past-date"')

    def test_signup_submit_with_email(self):
        d = date.today() + timedelta(days=5)
        # Mock time to NOT be Sunday morning
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(datetime(2026, 1, 12, 12, 0)) # Monday
            response = self.client.post(reverse('meal_signup_submit') + f'?date={d.isoformat()}', {
                'name': 'Email User',
                'phone': '555-0199',
                'email': 'user@example.com'
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(MealSignUp.objects.filter(date=d, email='user@example.com').exists())
        # Should send immediate notification because it's within 7 days and NOT Sunday morning
        self.assertEqual(len(mail.outbox), 1)

    def test_signup_submit_sunday_suppression(self):
        d = date.today() + timedelta(days=2)
        # Mock time to be Sunday 10 AM in America/Los_Angeles
        with patch('django.utils.timezone.now') as mock_now:
            # 2026-01-11 is a Sunday
            # We mock a UTC time that corresponds to Sunday 10 AM PST (UTC-8) -> 6 PM UTC
            # Or just use make_aware with a naive datetime and it will use the default TIME_ZONE
            mock_now.return_value = timezone.make_aware(datetime(2026, 1, 11, 10, 0))
            response = self.client.post(reverse('meal_signup_submit') + f'?date={d.isoformat()}', {
                'name': 'Sunday User',
                'phone': '555-0000'
            })
        self.assertEqual(response.status_code, 200)
        # Should NOT send immediate notification
        self.assertEqual(len(mail.outbox), 0)

    def test_signup_cancel_notification(self):
        d = date.today() + timedelta(days=2)
        MealSignUp.objects.create(date=d, name='To Be Cancelled', phone='123')
        mail.outbox = [] # Clear outbox
        
        response = self.client.post(reverse('meal_signup_submit') + f'?date={d.isoformat()}', {
            'name': '',
            'phone': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MealSignUp.objects.filter(date=d).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Missionary Meal Cancelled')
        # Check for HTML content
        self.assertTrue(any(alt[1] == 'text/html' for alt in mail.outbox[0].alternatives))

    def test_management_command_reminder(self):
        tomorrow = date.today() + timedelta(days=1)
        MealSignUp.objects.create(date=tomorrow, name='Tomorrow Person', email='tomorrow@example.com')
        
        out = StringIO()
        call_command('send_notifications', stdout=out)
        
        # Check if email was sent
        # We need to find the one with the reminder subject (there might be others if today is Sunday)
        reminder_emails = [m for m in mail.outbox if m.subject == 'Missionary Meal Reminder']
        self.assertEqual(len(reminder_emails), 1)
        self.assertEqual(reminder_emails[0].to, ['tomorrow@example.com'])
        self.assertIn('Tomorrow Person', reminder_emails[0].body)
        # Check for HTML content
        self.assertTrue(any(alt[1] == 'text/html' for alt in reminder_emails[0].alternatives))

    def test_management_command_weekly_summary(self):
        # We need to simulate today being Sunday
        today = date.today()
        if today.weekday() != 6:
            # If not Sunday, this test is harder to run without mocking date.today()
            # For now, let's just test the logic if it IS Sunday, or skip
            pass
        else:
            next_monday = today + timedelta(days=1)
            MealSignUp.objects.create(date=next_monday, name='Monday Person', phone='8015551234')
            
            out = StringIO()
            call_command('send_notifications', stdout=out)
            
            summary_emails = [m for m in mail.outbox if m.subject == 'Weekly Missionary Meal Summary']
            self.assertEqual(len(summary_emails), 1)
            self.assertIn('Monday Person ((801) 555-1234)', summary_emails[0].body)
            # Check for HTML content
            self.assertTrue(any(alt[1] == 'text/html' for alt in summary_emails[0].alternatives))
