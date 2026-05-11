from django import template

register = template.Library()


@register.filter
def indian_comma(value):
    """Format number with Indian digit grouping."""
    try:
        num = int(float(value))
    except (TypeError, ValueError):
        return value

    sign = "-" if num < 0 else ""
    digits = str(abs(num))
    if len(digits) <= 3:
        return f"{sign}{digits}"

    last_three = digits[-3:]
    rest = digits[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    return f"{sign}{','.join(groups)},{last_three}"
