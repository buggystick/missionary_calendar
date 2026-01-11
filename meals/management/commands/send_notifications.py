from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import date, timedelta
from meals.models import MealSignUp

class Command(BaseCommand):
    help = 'Sends meal reminders to users and weekly summaries to missionaries.'

    def handle(self, *args, **options):
        today = date.today()
        
        # 1. Reminders for tomorrow
        tomorrow = today + timedelta(days=1)
        tomorrow_signups = MealSignUp.objects.filter(date=tomorrow, is_unavailable=False).exclude(email='')
        for signup in tomorrow_signups:
            self.stdout.write(f"Sending reminder to {signup.email} for {tomorrow}")
            send_mail(
                'Missionary Meal Reminder',
                f'Hi {signup.name},\n\nThis is a reminder that you are signed up to feed the missionaries tomorrow, {tomorrow.strftime("%A, %B %d")}.\n\nThank you!',
                settings.DEFAULT_FROM_EMAIL,
                [signup.email],
                fail_silently=False,
            )

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
                        line = f"{d.strftime('%A, %b %d')}: {s.name} ({s.phone})"
                else:
                    line = f"{d.strftime('%A, %b %d')}: Available"
                summary_lines.append(line)
            
            summary_text = "\n".join(summary_lines)
            
            send_mail(
                'Weekly Missionary Meal Summary',
                summary_text,
                settings.DEFAULT_FROM_EMAIL,
                [settings.MISSIONARY_EMAIL],
                fail_silently=False,
            )
