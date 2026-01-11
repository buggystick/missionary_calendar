from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('signup-form/', views.meal_signup_form, name='meal_signup_form'),
    path('signup-submit/', views.meal_signup_submit, name='meal_signup_submit'),
]
