from django.core.mail import EmailMultiAlternatives
import phonenumbers
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
from .models import MealSignUp

def format_phone_number(phone_str):
    if not phone_str:
        return ""
    try:
        # Assuming US numbers for now, as it's a missionary calendar which is often used in US/Canada contexts.
        # We can make this more flexible if needed.
        parsed = phonenumbers.parse(phone_str, "US")
        if phonenumbers.is_valid_number(parsed):
            # If it's a US number, use NATIONAL format
            if parsed.country_code == 1:
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            else:
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except phonenumbers.NumberParseException:
        pass
    return phone_str

def is_valid_phone_number(phone_str):
    try:
        parsed = phonenumbers.parse(phone_str, "US")
        return phonenumbers.is_valid_number(parsed)
    except phonenumbers.NumberParseException:
        return False

def send_user_reminder(signup):
    subject = 'Missionary Meal Reminder'
    text_content = f'Hi {signup.name},\n\nThis is a reminder that you are signed up to feed the missionaries tomorrow, {signup.date.strftime("%A, %B %d")}.\n\nThank you!'
    html_content = render_to_string('meals/emails/user_reminder.html', {
        'name': signup.name,
        'date': signup.date,
    })
    bcc = [settings.ADMIN_BCC_EMAIL] if settings.ADMIN_BCC_EMAIL else []
    headers = {'X-PM-Message-Stream': settings.POSTMARK_MESSAGE_STREAM}
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [signup.email], bcc=bcc, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)

def send_missionary_update(date, status, name='', phone='', email='', cancelled=False, calendar_url=''):
    if cancelled:
        subject = 'Missionary Meal Cancelled'
        text_content = f'The meal appointment for {date} has been cancelled.'
    else:
        subject = 'Missionary Meal Update'
        text_content = f'An appointment for {date} has been updated: {status}'

    html_content = render_to_string('meals/emails/missionary_update.html', {
        'date': date,
        'status': status,
        'name': name,
        'phone': phone,
        'email': email,
        'cancelled': cancelled,
        'calendar_url': calendar_url
    })
    bcc = [settings.ADMIN_BCC_EMAIL] if settings.ADMIN_BCC_EMAIL else []
    headers = {'X-PM-Message-Stream': settings.POSTMARK_MESSAGE_STREAM}
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [settings.MISSIONARY_EMAIL], bcc=bcc, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)

def send_weekly_summary(today, calendar_url=None):
    if calendar_url is None:
        calendar_url = settings.CALENDAR_EXTERNAL_URL
    # Get signups for 14 days, starting from the most recent Sunday
    # weekday() returns 0 for Monday, 6 for Sunday
    # If today is Sunday, we start from today.
    # If today is Monday(0), we go back 1 day.
    # If today is Saturday(5), we go back 6 days.
    days_since_sunday = (today.weekday() + 1) % 7
    start_date = today - timedelta(days=days_since_sunday)
    end_date = start_date + timedelta(days=13)

    week_signups = MealSignUp.objects.filter(date__range=[start_date, end_date]).order_by('date')

    summary_lines = [f"Meal Signups for {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}:\n"]

    # Create a dictionary for easy lookup
    signups_by_date = {s.date: s for s in week_signups}

    schedule_data = []
    for i in range(14):
        d = start_date + timedelta(days=i)
        s = signups_by_date.get(d)
        if s:
            if s.is_unavailable:
                line = f"{d.strftime('%a, %b %d')}: UNAVAILABLE"
            else:
                formatted_phone = format_phone_number(s.phone)
                line = f"{d.strftime('%a, %b %d')}: {s.name} ({formatted_phone})"

            schedule_data.append({
                'date': d,
                'is_unavailable': s.is_unavailable,
                'name': s.name,
                'phone': format_phone_number(s.phone)
            })
        else:
            line = f"{d.strftime('%a, %b %d')}: Available"
            schedule_data.append({
                'date': d,
                'is_unavailable': False,
                'name': None
            })
        summary_lines.append(line)

    summary_text = "\n".join(summary_lines)

    html_content = render_to_string('meals/emails/weekly_summary.html', {
        'start_date': start_date,
        'end_date': end_date,
        'schedule': schedule_data,
        'calendar_url': calendar_url
    })

    subject = 'Missionary Meal Summary'
    bcc = [settings.ADMIN_BCC_EMAIL] if settings.ADMIN_BCC_EMAIL else []
    headers = {'X-PM-Message-Stream': settings.POSTMARK_MESSAGE_STREAM}
    msg = EmailMultiAlternatives(subject, summary_text, settings.DEFAULT_FROM_EMAIL, [settings.MISSIONARY_EMAIL], bcc=bcc, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
