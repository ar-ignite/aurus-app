from django.core.exceptions import PermissionDenied
from functools import wraps

from .models import Menu

def check_menu_permission(permission_codename):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            menu_id = kwargs.get('menu_id')
            if not menu_id:
                raise ValueError("menu_id is required")
            
            # Check if user has the required permission for this menu
            menu = Menu.objects.get(id=menu_id)
            permission_name = f'menu.{permission_codename}_menu'
            
            if not request.user.has_perm(permission_name, menu):
                raise PermissionDenied
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator