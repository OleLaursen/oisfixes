from django import template
 
register = template.Library()
 
@register.filter
def truncate(value, size):
    size = int(size)
    if len(value) > size and size > 3:
        return value[:(size-3)] + '...'
    else:
        return value[:size]
    
truncate.is_safe = True
