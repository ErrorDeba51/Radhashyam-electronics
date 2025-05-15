# cart/templatetags/cart_tags.py
from django import template

register = template.Library()

# Add your custom template tags here


@register.filter
def currency_format(value):
    """Format numbers as currency"""
    return f"₹{value:,.2f}"
