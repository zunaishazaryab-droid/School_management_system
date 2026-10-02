from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Decorator to restrict view access to users with specific roles.
    Example: @role_required('ADMIN', 'PRINCIPAL')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You do not have permission to access this module.")
            if getattr(request.user, 'is_student', False) or getattr(request.user, 'is_parent', False):
                return redirect('students:student_dashboard')
            return redirect('core:dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Restricts view access to Admin/Owner or Superuser."""
    return role_required('ADMIN')(view_func)


def principal_required(view_func):
    """Restricts view access to Principal or Admin."""
    return role_required('ADMIN', 'PRINCIPAL')(view_func)


def coordinator_required(view_func):
    """Restricts view access to Coordinator, Principal or Admin."""
    return role_required('ADMIN', 'PRINCIPAL', 'COORDINATOR')(view_func)


def accountant_required(view_func):
    """Restricts view access to Accountant/Admin/Principal/Coordinator."""
    return role_required('ADMIN', 'PRINCIPAL', 'COORDINATOR')(view_func)


def teacher_required(view_func):
    """Restricts view access to Teacher, Coordinator, Principal or Admin."""
    return role_required('ADMIN', 'PRINCIPAL', 'COORDINATOR', 'TEACHER')(view_func)

