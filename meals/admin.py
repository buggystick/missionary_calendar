from django.contrib import admin
from .models import MealSignUp

@admin.register(MealSignUp)
class MealSignUpAdmin(admin.ModelAdmin):
    list_display = ('date', 'name', 'phone', 'email', 'is_unavailable')
    list_filter = ('is_unavailable', 'date')
    ordering = ('-date',)
    search_fields = ('name', 'email', 'phone')
