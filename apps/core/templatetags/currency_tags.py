from django import template

from apps.core.utils import format_uzs

register = template.Library()

@register.filter(name='uzs')
def uzs(value):
    return format_uzs(value)
