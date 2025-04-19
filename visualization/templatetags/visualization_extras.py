from django import template

register = template.Library()

@register.filter
def get_item(lst, i):
    """
    Gets an item from a list by index or a value from a dictionary by key.
    Usage: {{ mylist|get_item:index }} or {{ mydict|get_item:key }}
    """
    try:
        if isinstance(lst, list):
            return lst[i]
        elif isinstance(lst, dict):
            return lst.get(i)
        return None
    except (IndexError, KeyError, TypeError):
        return None
