"""
Custom template tags for Gallery app
"""
from django import template

register = template.Library()


@register.filter
def filesizeformat(value):
    """Format file size in human-readable format"""
    if value is None:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"
