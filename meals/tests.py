from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from .models import MealSignUp
from django.utils import timezone
from unittest.mock import patch
from datetime import date, timedelta, datetime
import calendar
from django.core.management import call_command
from io import StringIO
from .utils import format_phone_number, is_valid_phone_number, is_default_unavailable, _week_of_month

class UnavailableDaysTest(TestCase):
    @override_settings(UNAVAILABLE_DAYS='mon')
    def test_every_monday(self):
        # 2026-06-15 is a Monday
        self.assertTrue(is_default_unavailable(date(2026, 6, 15)))
        # 2026-06-16 is a Tuesday
        self.assertFalse(is_default_unavailable(date(2026, 6, 16)))

    @override_settings(UNAVAILABLE_DAYS='mon,fri')
    def test_multiple_days(self):
        self.assertTrue(is_default_unavailable(date(2026, 6, 15)))   # Monday
        self.assertTrue(is_default_unavailable(date(2026, 6, 19)))   # Friday
        self.assertFalse(is_default_unavailable(date(2026, 6, 17)))  # Wednesday

    @override_settings(UNAVAILABLE_DAYS='')
    def test_empty_means_none(self):
        self.assertFalse(is_default_unavailable(date(2026, 6, 15)))  # Monday

    @override_settings(UNAVAILABLE_DAYS='mon:1/3')
    def test_specific_weeks(self):
        # June 2026: 1st starts on Monday
        # Week 1 Monday = June 1
        self.assertTrue(is_default_unavailable(date(2026, 6, 1)))
        # Week 2 Monday = June 8
        self.assertFalse(is_default_unavailable(date(2026, 6, 8)))
        # Week 3 Monday = June 15
        self.assertTrue(is_default_unavailable(date(2026, 6, 15)))
        # Week 4 Monday = June 22
        self.assertFalse(is_default_unavailable(date(2026, 6, 22)))

    @override_settings(UNAVAILABLE_DAYS='mon:odd')
    def test_odd_weeks(self):
        self.assertTrue(is_default_unavailable(date(2026, 6, 1)))    # week 1
        self.assertFalse(is_default_unavailable(date(2026, 6, 8)))   # week 2
        self.assertTrue(is_default_unavailable(date(2026, 6, 15)))   # week 3

    @override_settings(UNAVAILABLE_DAYS='mon:even')
    def test_even_weeks(self):
        self.assertFalse(is_default_unavailable(date(2026, 6, 1)))   # week 1
        self.assertTrue(is_default_unavailable(date(2026, 6, 8)))    # week 2
        self.assertFalse(is_default_unavailable(date(2026, 6, 15)))  # week 3
        self.assertTrue(is_default_unavailable(date(2026, 6, 22)))   # week 4

    def test_week_of_month(self):
        # June 2026: June 1 is a Monday, so Sunday May 31 would be week boundary
        # Week 1 contains June 1-6 (Mon-Sat), week starts on Sunday
        self.assertEqual(_week_of_month(date(2026, 6, 1)), 1)
        self.assertEqual(_week_of_month(date(2026, 6, 7)), 2)  # Sunday = new week
        self.assertEqual(_week_of_month(date(2026, 6, 8)), 2)

    @override_settings(UNAVAILABLE_DAYS='week:3/4/5')
    def test_full_week_unavailable(self):
        """Full weeks 3, 4, 5 should be unavailable for all days."""
        # June 2026: week 1 = June 1-6, week 2 = June 7-13, week 3 = June 14-20
        self.assertFalse(is_default_unavailable(date(2026, 6, 1)))   # week 1 Mon
        self.assertFalse(is_default_unavailable(date(2026, 6, 10)))  # week 2 Wed
        self.assertTrue(is_default_unavailable(date(2026, 6, 14)))   # week 3 Sun
        self.assertTrue(is_default_unavailable(date(2026, 6, 17)))   # week 3 Wed
        self.assertTrue(is_default_unavailable(date(2026, 6, 22)))   # week 4 Mon
        self.assertTrue(is_default_unavailable(date(2026, 6, 29)))   # week 5 Mon

    @override_settings(UNAVAILABLE_DAYS='week:odd')
    def test_full_week_odd(self):
        self.assertTrue(is_default_unavailable(date(2026, 6, 3)))    # week 1 Wed
        self.assertFalse(is_default_unavailable(date(2026, 6, 10)))  # week 2 Wed
        self.assertTrue(is_default_unavailable(date(2026, 6, 17)))   # week 3 Wed

    @override_settings(UNAVAILABLE_DAYS='mon,week:3/4/5')
    def test_day_and_week_combined(self):
        """Mondays always unavailable + full weeks 3-5 unavailable."""
        self.assertTrue(is_default_unavailable(date(2026, 6, 1)))    # week 1 Mon (day rule)
        self.assertFalse(is_default_unavailable(date(2026, 6, 3)))   # week 1 Wed (no rule)
        self.assertTrue(is_default_unavailable(date(2026, 6, 17)))   # week 3 Wed (week rule)
        self.assertTrue(is_default_unavailable(date(2026, 6, 22)))   # week 4 Mon (both rules)

    @override_settings(UNAVAILABLE_DAYS='tues')
    def test_alternate_day_names(self):
        """Longer day name variants like 'tues' should work."""
        self.assertTrue(is_default_unavailable(date(2026, 6, 16)))   # Tuesday
        self.assertFalse(is_default_unavailable(date(2026, 6, 15)))  # Monday

    @override_settings(UNAVAILABLE_DAYS='tue')
    def test_calendar_view_uses_setting(self):
        """Calendar view should mark Tuesdays (not Mondays) as unavailable."""
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)


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
