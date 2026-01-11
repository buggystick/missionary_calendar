from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import MealSignUp
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
                week_days.append({
                    'date': d,
                    'signup': signups.get(d)
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
    return render(request, 'meals/signup_form.html', {'date': d, 'signup': signup})

def meal_signup_submit(request):
    date_str = request.GET.get('date')
    d = date.fromisoformat(date_str)
    name = request.POST.get('name', '')
    phone = request.POST.get('phone', '')
    is_unavailable = request.POST.get('is_unavailable') == 'on'
    
    if not is_unavailable and not name and not phone:
        # If it's not unavailable and name/phone are empty, we revert to default (delete)
        MealSignUp.objects.filter(date=d).delete()
        return render(request, 'meals/signup_cell.html', {'signup': None, 'date': d})

    signup, created = MealSignUp.objects.update_or_create(
        date=d,
        defaults={
            'name': name if not is_unavailable else '',
            'phone': phone if not is_unavailable else '',
            'is_unavailable': is_unavailable
        }
    )
    
    return render(request, 'meals/signup_cell.html', {'signup': signup})
