
# templatetags/form_extras.py
from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})


@register.filter
def attr(field, attr_string):
    attr_name, attr_value = attr_string.split(':')
    return field.as_widget(attrs={attr_name: attr_value})
    
# your_app/templatetags/custom_filters.py
from django import template
from django.utils import timezone
import pytz

register = template.Library()

@register.filter
def utc(value):
    """Convert datetime to UTC timezone."""
    if value is None:
        return value
    
    # If the datetime is naive (no timezone), make it aware
    if timezone.is_naive(value):
        # Assuming naive datetime is in system timezone
        value = timezone.make_aware(value, timezone.get_current_timezone())
    
    # Convert to UTC
    return timezone.localtime(value).astimezone(pytz.UTC)

@register.filter(name='localtime')
def local_time(value):
    """Convert datetime to local timezone."""
    if value is None:
        return value
    return timezone.localtime(value)

