from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from mptt.admin import DraggableMPTTAdmin
from .models import CustomUser, Client, Application, Menu, MenuPermission

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'client', 'application', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('middle_name', 'client', 'application')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('middle_name', 'client', 'application')}),
    )

@admin.register(Menu)
class MenuAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "name"
    list_display = (
        'tree_actions',
        'indented_title',
        'application',
        'path',
        'order',
    )
    list_filter = ('application',)
    
    expand_tree_by_default = True
    search_fields = ['name', 'path']  # Add this for autocomplete to work
    list_display_links = ('indented_title',)
    # list_display = ('name', 'application', 'path', 'order', 'parent')
    list_filter = ('application',)
    expand_tree_by_default = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('application', 'tree_id', 'lft')

    def indented_title(self, instance):
        return instance.get_admin_tree_title()
    indented_title.short_description = 'Menu Name'

    fieldsets = (
        (None, {
            'fields': ('application', 'name', 'description')
        }),
        ('Navigation', {
            'fields': ('parent', 'path', 'order')
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/custom_mptt.css',)
        }

@admin.register(MenuPermission)
class MenuPermissionAdmin(admin.ModelAdmin):
    list_display = ('menu', 'group', 'permission')
    list_filter = ('group', 'menu', 'permission')
    
    # Now all referenced models have search_fields defined
    raw_id_fields = ['menu', 'group', 'permission']

admin.site.register(Client)
admin.site.register(Application)
from django.contrib.auth.models import Permission
admin.site.register(Permission)

from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from django.contrib import admin
from .models import Menu, MenuPermission

# Unregister the original GroupAdmin
admin.site.unregister(Group)

# Create a custom GroupAdmin with search_fields
@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    search_fields = ['name']  # Add this for autocomplete to work

    
admin.site.unregister(Permission)
# You'll also need to register a custom Permission admin for autocomplete
class PermissionAdmin(admin.ModelAdmin):
    search_fields = ['name', 'codename']
    list_display = ['name', 'codename', 'content_type']

admin.site.register(Permission, PermissionAdmin)


    