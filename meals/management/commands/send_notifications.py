from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import date, timedelta
import time
from meals.models import MealSignUp
from meals.utils import format_phone_number

class Command(BaseCommand):
    help = 'Sends meal reminders to users and weekly summaries to missionaries.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send sample emails of all types to test configuration',
        )

    def handle(self, *args, **options):
        if options['test']:
            self.send_test_emails()
            return

        today = date.today()
        
        # 1. Reminders for tomorrow
        tomorrow = today + timedelta(days=1)
        tomorrow_signups = MealSignUp.objects.filter(date=tomorrow, is_unavailable=False).exclude(email='')
        for signup in tomorrow_signups:
            self.stdout.write(f"Sending reminder to {signup.email} for {tomorrow}")
            subject = 'Missionary Meal Reminder'
            text_content = f'Hi {signup.name},\n\nThis is a reminder that you are signed up to feed the missionaries tomorrow, {tomorrow.strftime("%A, %B %d")}.\n\nThank you!'
            html_content = render_to_string('meals/emails/user_reminder.html', {
                'name': signup.name,
                'date': tomorrow,
            })
            bcc = [settings.ADMIN_BCC_EMAIL] if settings.ADMIN_BCC_EMAIL else []
            headers = {'X-PM-Message-Stream': settings.POSTMARK_MESSAGE_STREAM}
            msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [signup.email], bcc=bcc, headers=headers)
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

        # 2. Weekly summary for missionaries (Run on Sunday evening)
        # Note: If running via cron, ensure it runs once on Sunday.
        if today.weekday() == 6: # 6 is Sunday
            self.stdout.write("Generating weekly summary for missionaries")
            # Get signups for the coming week (Monday to Sunday)
            next_monday = today + timedelta(days=1)
            next_sunday = today + timedelta(days=7)
            
            week_signups = MealSignUp.objects.filter(date__range=[next_monday, next_sunday]).order_by('date')
            
            summary_lines = [f"Meal Signups for the week of {next_monday.strftime('%B %d')} - {next_sunday.strftime('%B %d')}:\n"]
            
            # Create a dictionary for easy lookup
            signups_by_date = {s.date: s for s in week_signups}
            
            for i in range(1, 8):
                d = today + timedelta(days=i)
                s = signups_by_date.get(d)
                if s:
                    if s.is_unavailable:
                        line = f"{d.strftime('%A, %b %d')}: UNAVAILABLE"
                    else:
                        formatted_phone = format_phone_number(s.phone)
                        line = f"{d.strftime('%A, %b %d')}: {s.name} ({formatted_phone})"
                else:
                    line = f"{d.strftime('%A, %b %d')}: Available"
                summary_lines.append(line)
            
            summary_text = "\n".join(summary_lines)
            
            # Prepare schedule for HTML template
            schedule_data = []
            for i in range(1, 8):
                d = today + timedelta(days=i)
                s = signups_by_date.get(d)
                if s:
                    schedule_data.append({
                        'date': d,
                        'is_unavailable': s.is_unavailable,
                        'name': s.name,
                        'phone': format_phone_number(s.phone)
                    })
                else:
                    schedule_data.append({
                        'date': d,
                        'is_unavailable': False,
                        'name': None
                    })

            html_content = render_to_string('meals/emails/weekly_summary.html', {
                'start_date': next_monday,
                'end_date': next_sunday,
                'schedule': schedule_data,
                'calendar_url': 'https://missionaries.farmingtonward.church' # Use settings if available, or a placeholder
            })
            
            subject = 'Weekly Missionary Meal Summary'
            bcc = [settings.ADMIN_BCC_EMAIL] if settings.ADMIN_BCC_EMAIL else []
            headers = {'X-PM-Message-Stream': settings.POSTMARK_MESSAGE_STREAM}
            msg = EmailMultiAlternatives(subject, summary_text, settings.DEFAULT_FROM_EMAIL, [settings.MISSIONARY_EMAIL], bcc=bcc, headers=headers)
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

    def send_test_emails(self):
        self.stdout.write("Sending test emails of all types...")
        self.stdout.write("(Adding 10-second delay between emails for Mailtrap rate limiting)")
        test_date = date.today() + timedelta(days=1)
        test_email = settings.MISSIONARY_EMAIL # Use missionary email as the recipient for all test emails
        
        # 1. Test User Reminder
        self.stdout.write(f"- Sending sample User Reminder to {test_email}")
        subject = '[TEST] Missionary Meal Reminder'
        text_content = f'Hi Test User,\n\nThis is a sample reminder for {test_date}.'
        html_content = render_to_string('meals/emails/user_reminder.html', {
            'name': 'Test User',
            'date': test_date,
        })
        bcc = [settings.ADMIN_BCC_EMAIL] if settings.ADMIN_BCC_EMAIL else []
        headers = {'X-PM-Message-Stream': settings.POSTMARK_MESSAGE_STREAM}
        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [test_email], bcc=bcc, headers=headers)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        time.sleep(10)

        # 2. Test Missionary Update (Sign up)
        self.stdout.write(f"- Sending sample Missionary Update (Sign up) to {settings.MISSIONARY_EMAIL}")
        subject = '[TEST] Missionary Meal Update'
        status = "signed up by Test Person (555-0100)"
        text_content = f'An appointment for {test_date} has been updated: {status}'
        html_content = render_to_string('meals/emails/missionary_update.html', {
            'date': test_date,
            'status': status,
            'name': 'Test Person',
            'phone': '555-0100',
            'cancelled': False,
            'calendar_url': 'http://localhost:8000/'
        })
        bcc = [settings.ADMIN_BCC_EMAIL] if settings.ADMIN_BCC_EMAIL else []
        headers = {'X-PM-Message-Stream': settings.POSTMARK_MESSAGE_STREAM}
        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [settings.MISSIONARY_EMAIL], bcc=bcc, headers=headers)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        time.sleep(10)

        # 3. Test Missionary Update (Cancellation)
        self.stdout.write(f"- Sending sample Missionary Update (Cancellation) to {settings.MISSIONARY_EMAIL}")
        subject = '[TEST] Missionary Meal Cancelled'
        text_content = f'The meal appointment for {test_date} has been cancelled.'
        html_content = render_to_string('meals/emails/missionary_update.html', {
            'date': test_date,
            'cancelled': True,
            'calendar_url': 'http://localhost:8000/'
        })
        bcc = [settings.ADMIN_BCC_EMAIL] if settings.ADMIN_BCC_EMAIL else []
        headers = {'X-PM-Message-Stream': settings.POSTMARK_MESSAGE_STREAM}
        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [settings.MISSIONARY_EMAIL], bcc=bcc, headers=headers)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        time.sleep(10)

        # 4. Test Weekly Summary
        self.stdout.write(f"- Sending sample Weekly Summary to {settings.MISSIONARY_EMAIL}")
        subject = '[TEST] Weekly Missionary Meal Summary'
        schedule_data = [
            {'date': test_date, 'is_unavailable': False, 'name': 'Person A', 'phone': '111'},
            {'date': test_date + timedelta(days=1), 'is_unavailable': True},
            {'date': test_date + timedelta(days=2), 'is_unavailable': False, 'name': None},
        ]
        text_content = "Sample Weekly Summary Content"
        html_content = render_to_string('meals/emails/weekly_summary.html', {
            'start_date': test_date,
            'end_date': test_date + timedelta(days=6),
            'schedule': schedule_data,
            'calendar_url': 'http://localhost:8000/'
        })
        bcc = [settings.ADMIN_BCC_EMAIL] if settings.ADMIN_BCC_EMAIL else []
        headers = {'X-PM-Message-Stream': settings.POSTMARK_MESSAGE_STREAM}
        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [settings.MISSIONARY_EMAIL], bcc=bcc, headers=headers)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        self.stdout.write(self.style.SUCCESS("All test emails sent successfully!"))
