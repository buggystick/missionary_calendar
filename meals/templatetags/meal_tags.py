from django import template
from meals.utils import format_phone_number

register = template.Library()

@register.filter(name='format_phone')
def format_phone(value):
    return format_phone_number(value)
