from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone
from .models import MealSignUp
from .utils import (
    format_phone_number, is_valid_phone_number, 
    send_missionary_update, is_default_unavailable
)
import calendar
from datetime import date, timedelta

def get_calendar_context(year, month):
    cal = calendar.Calendar(firstweekday=6) # Sunday start
    month_days = cal.monthdatescalendar(year, month)
    
    signups = {s.date: s for s in MealSignUp.objects.filter(date__year=year, date__month=month)}
    
    calendar_weeks = []
    for week in month_days:
        week_days = []
        for d in week:
            if d.month == month:
                signup = signups.get(d)
                if signup is None and is_default_unavailable(d):
                    signup = MealSignUp(date=d, is_unavailable=True)
                week_days.append({
                    'date': d,
                    'signup': signup
                })
            else:
                week_days.append({'date': None})
        calendar_weeks.append(week_days)
    
    today = date.today()
    current_month_first_day = today.replace(day=1)
    next_month_first_day = (current_month_first_day + timedelta(days=32)).replace(day=1)
    
    view_date = date(year, month, 1)
    
    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'calendar_weeks': calendar_weeks,
        'today': today,
    }

    if view_date == current_month_first_day:
        context['nav_link'] = {
            'year': next_month_first_day.year,
            'month': next_month_first_day.month,
            'label': 'Next Month'
        }
    elif view_date == next_month_first_day:
        context['nav_link'] = {
            'year': current_month_first_day.year,
            'month': current_month_first_day.month,
            'label': 'Previous Month'
        }
    
    return context

def calendar_view(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    context = get_calendar_context(year, month)
    return render(request, 'meals/calendar.html', context)

def meal_signup_form(request):
    date_str = request.GET.get('date')
    d = date.fromisoformat(date_str)
    signup = MealSignUp.objects.filter(date=d).first()
    if signup is None and is_default_unavailable(d):
        signup = MealSignUp(date=d, is_unavailable=True)
    return render(request, 'meals/signup_form.html', {'date': d, 'signup': signup})

def meal_signup_submit(request):
    date_str = request.GET.get('date')
    d = date.fromisoformat(date_str)
    name = request.POST.get('name', '')
    phone = request.POST.get('phone', '')
    email = request.POST.get('email', '')
    is_unavailable_val = request.POST.get('is_unavailable')
    is_unavailable = is_unavailable_val == 'on'
    should_delete = is_unavailable_val == 'delete'
    
    if not is_unavailable and name and phone:
        if not is_valid_phone_number(phone):
            pass
        else:
            phone = format_phone_number(phone)
    
    if not is_unavailable and not name and not phone:
        if should_delete or not is_default_unavailable(d):
            # If it's not unavailable and name/phone are empty, we revert to default (delete)
            # EXCEPT for default-unavailable days, where "revert" means go back to Unavailable,
            # while an empty save should make it explicitly Available.
            MealSignUp.objects.filter(date=d).delete()
            
            # Immediate notification for changes in the current week
            today = date.today()
            # Suppress emails on Sundays before 3 PM (Church hours)
            now = timezone.localtime(timezone.now())
            is_sunday_morning = now.weekday() == 6 and now.hour < 15
            
            if today <= d <= today + timedelta(days=7) and not is_sunday_morning:
                send_missionary_update(
                    date=d,
                    status='cancelled',
                    cancelled=True,
                    calendar_url=request.build_absolute_uri('/')
                )
                
            signup = None
            if is_default_unavailable(d):
                signup = MealSignUp(date=d, is_unavailable=True)
            return render(request, 'meals/signup_cell.html', {'signup': signup, 'date': d})
        else:
            # It's a default-unavailable day and we want to explicitly make it available (no name/phone)
            pass

    signup, created = MealSignUp.objects.update_or_create(
        date=d,
        defaults={
            'name': name if not is_unavailable else '',
            'phone': phone if not is_unavailable else '',
            'email': email if not is_unavailable else '',
            'is_unavailable': is_unavailable
        }
    )
    
    # Immediate notification for changes in the current week
    today = date.today()
    # Suppress emails on Sundays before 3 PM (Church hours)
    now = timezone.localtime(timezone.now())
    is_sunday_morning = now.weekday() == 6 and now.hour < 15

    if today <= d <= today + timedelta(days=7) and not is_sunday_morning:
        if is_unavailable:
            status = "marked as unavailable"
        elif name:
            status = f"signed up by {name} ({phone})"
        else:
            status = "marked as available"
            
        send_missionary_update(
            date=d,
            status=status,
            name=name if not is_unavailable else '',
            phone=phone if not is_unavailable else '',
            email=email if not is_unavailable else '',
            cancelled=False,
            calendar_url=request.build_absolute_uri('/')
        )
    
    return render(request, 'meals/signup_cell.html', {'signup': signup})
