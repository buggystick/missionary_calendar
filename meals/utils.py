from django.core.mail import EmailMultiAlternatives
import calendar as cal_module
import phonenumbers
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
from .models import MealSignUp

DAY_NAME_TO_WEEKDAY = {
    'mon': 0, 'monday': 0,
    'tue': 1, 'tues': 1, 'tuesday': 1,
    'wed': 2, 'wednesday': 2,
    'thu': 3, 'thur': 3, 'thurs': 3, 'thursday': 3,
    'fri': 4, 'friday': 4,
    'sat': 5, 'saturday': 5,
    'sun': 6, 'sunday': 6,
}

def _week_of_month(d):
    """Return the 1-based week-of-month for a date (weeks start on Sunday)."""
    first = d.replace(day=1)
    # Shift so Sunday=0
    first_dow = (first.weekday() + 1) % 7
    return (d.day + first_dow - 1) // 7 + 1

def _parse_unavailable_rules(raw):
    """Parse the UNAVAILABLE_DAYS setting string into a list of rule tuples.
    
    Returns a list of tuples:
      - (weekday, week_filter) for day-specific rules
      - ('week', frozenset_of_weeks) for full-week rules
    
    week_filter is None (every week), 'odd', 'even', or a frozenset of ints.
    """
    rules = []
    if not raw or not raw.strip():
        return rules
    for token in raw.split(','):
        token = token.strip().lower()
        if not token:
            continue
        # Full-week rules: "week:3/4/5" marks all days in those weeks unavailable
        if token.startswith('week:'):
            qualifier = token[5:].strip()
            if qualifier in ('odd', 'even'):
                rules.append(('week', qualifier))
            else:
                weeks = frozenset(int(w.strip()) for w in qualifier.split('/') if w.strip().isdigit())
                if weeks:
                    rules.append(('week', weeks))
            continue
        if ':' in token:
            day_part, qualifier = token.split(':', 1)
            day_part = day_part.strip()
            qualifier = qualifier.strip()
            weekday = DAY_NAME_TO_WEEKDAY.get(day_part)
            if weekday is None:
                continue
            if qualifier in ('odd', 'even'):
                rules.append((weekday, qualifier))
            else:
                weeks = frozenset(int(w.strip()) for w in qualifier.split('/') if w.strip().isdigit())
                if weeks:
                    rules.append((weekday, weeks))
        else:
            weekday = DAY_NAME_TO_WEEKDAY.get(token)
            if weekday is not None:
                rules.append((weekday, None))
    return rules

def is_default_unavailable(d):
    """Check if a date should be marked unavailable by default based on UNAVAILABLE_DAYS setting."""
    rules = _parse_unavailable_rules(getattr(settings, 'UNAVAILABLE_DAYS', ''))
    if not rules:
        return False
    weekday = d.weekday()
    wom = None  # lazy compute
    for rule_key, week_filter in rules:
        if rule_key == 'week':
            # Full-week rule: applies to all days in matching weeks
            if wom is None:
                wom = _week_of_month(d)
            if week_filter == 'odd' and wom % 2 == 1:
                return True
            if week_filter == 'even' and wom % 2 == 0:
                return True
            if isinstance(week_filter, frozenset) and wom in week_filter:
                return True
        else:
            # Day-specific rule
            if weekday != rule_key:
                continue
            if week_filter is None:
                return True
            if wom is None:
                wom = _week_of_month(d)
            if week_filter == 'odd' and wom % 2 == 1:
                return True
            if week_filter == 'even' and wom % 2 == 0:
                return True
            if isinstance(week_filter, frozenset) and wom in week_filter:
                return True
    return False

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
