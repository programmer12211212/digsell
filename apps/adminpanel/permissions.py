"""Admin panel access: staff flag yoki platforma rollari."""

ADMIN_ROLES = frozenset({'ADMIN', 'SUPER_ADMIN', 'MODERATOR'})


def is_admin_user(user):
    if not user or not user.is_authenticated:
        return False
    return bool(user.is_staff or getattr(user, 'role', None) in ADMIN_ROLES)


def staff_required(view_func):
    from django.contrib.auth.decorators import user_passes_test
    return user_passes_test(is_admin_user)(view_func)
