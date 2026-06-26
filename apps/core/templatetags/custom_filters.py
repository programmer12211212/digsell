from django import template

register = template.Library()


@register.filter(name='length_is')
def length_is(value, arg):
    """Return True if len(value) == int(arg). Safe on non-iterables.

    Usage: {{ mylist|length_is:'1' }}
    """
    try:
        expected = int(arg)
    except Exception:
        return False

    try:
        return len(value) == expected
    except Exception:
        return False
