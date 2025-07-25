from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from functools import wraps

def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied("User not authenticated")
            if not hasattr(user, 'userprofile'):
                raise PermissionDenied("User has no profile")

            role = user.userprofile.role
            if role not in allowed_roles:
                # Custom message passed to template
                raise PermissionDenied(f"Your role '{role}' does not have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view

    return decorator
