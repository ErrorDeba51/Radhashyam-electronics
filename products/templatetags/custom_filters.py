# radhashyam/products/templatetags/custom_filters.py

from django import template

register = template.Library()


@register.filter
def in_getlist(value, param_name):
    """Check if value exists in request.GET.getlist(param_name)"""
    request = template.Variable('request').resolve({})
    return str(value) in request.GET.getlist(param_name)
