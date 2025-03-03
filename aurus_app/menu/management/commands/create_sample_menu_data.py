from django.core.management.base import BaseCommand

# Sample data creation script - Run this in a management command or shell
from django.contrib.auth.models import Group
from menu.models import Role, MenuRole, CustomUser, Application, Menu, Client



def create_sample_data():
    # Create an application
    app, _ = Application.objects.get_or_create(name="Mortgage Document System")
    client, _ = Client.objects.get_or_create(name="Test Client 123")

    # Create roles (linked to Django groups)
    ceo_group, _ = Group.objects.get_or_create(name='CEO')
    cto_group, _ = Group.objects.get_or_create(name='CTO')
    employee_group, _ = Group.objects.get_or_create(name='Employee')
    
    ceo_role, _ = Role.objects.get_or_create(
        name='CEO', 
        defaults={'group': ceo_group, 'description': 'Chief Executive Officer'}
    )
    
    cto_role, _ = Role.objects.get_or_create(
        name='CTO', 
        defaults={'group': cto_group, 'description': 'Chief Technology Officer'}
    )
    
    employee_role, _ = Role.objects.get_or_create(
        name='Employee', 
        defaults={'group': employee_group, 'description': 'Regular Employee'}
    )
    
    # Create users with roles
    uday, _ = CustomUser.objects.get_or_create(
        username='uday',
        defaults={
            'client': client,
            'application': app,
            'email': 'uday@example.com',
            'first_name': 'Uday',
            'last_name': 'CEO',
            'role': ceo_role,
            'is_active': True
        }
    )
    uday.set_password('password123')
    uday.save()


    # Create users with roles
    prakash, _ = CustomUser.objects.get_or_create(
        username='prakash',
        defaults={
            'client': client,
            'application': app,
            'email': 'prakash@example.com',
            'first_name': 'Prakash',
            'last_name': 'CTO',
            'role': cto_role,
            'is_active': True
        }
    )
    prakash.set_password('password123')
    prakash.save()
    
    aniruddha, _ = CustomUser.objects.get_or_create(
        username='aniruddha',
        defaults={
            'client': client,
            'application': app,
            'email': 'aniruddha@example.com',
            'first_name': 'Aniruddha',
            'last_name': 'CTO',
            'role': cto_role,
            'is_active': True
        }
    )
    aniruddha.set_password('password123')
    aniruddha.save()
    
    testuser, _ = CustomUser.objects.get_or_create(
        username='testuser1',
        defaults={
            'client': client,
            'application': app,
            'email': 'testuser1@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': employee_role,
            'is_active': True
        }
    )
    testuser.set_password('password123')
    testuser.save()
    
    
    
    # Create menu structure
    # Level 1 Menus
    dashboard, _ = Menu.objects.get_or_create(
        name="Dashboard",
        defaults={
            'application': app,
            'path': "/dashboard",
            'order': 1
        }
    )
    
    doc_management, _ = Menu.objects.get_or_create(
        name="Document Management",
        defaults={
            'application': app,
            'path': "/document-management",
            'order': 2
        }
    )
    
    ai_analytics, _ = Menu.objects.get_or_create(
        name="AI & Analytics",
        defaults={
            'application': app,
            'path': "/analytics",
            'order': 3
        }
    )
    
    compliance, _ = Menu.objects.get_or_create(
        name="Compliance",
        defaults={
            'application': app,
            'path': "/compliance",
            'order': 4
        }
    )
    
    user_management, _ = Menu.objects.get_or_create(
        name="User Management",
        defaults={
            'application': app,
            'path': "/user-management",
            'order': 5
        }
    )
    
    support, _ = Menu.objects.get_or_create(
        name="Support",
        defaults={
            'application': app,
            'path': "/support",
            'order': 6
        }
    )

    finance, _ = Menu.objects.get_or_create(
        name="Finance",
        defaults={
            'application': app,
            'path': "/support",
            'order': 7
        }
    )

    accounting, _ = Menu.objects.get_or_create(
        name="Accounting",
        defaults={
            'application': app,
            'path': "/support",
            'order': 8
        }
    )
    
    # Level 2 Menus - Document Management
    upload_doc, _ = Menu.objects.get_or_create(
        name="Upload Document",
        defaults={
            'application': app,
            'path': "/document-management/upload",
            'order': 1,
            'parent': doc_management
        }
    )
    
    view_doc, _ = Menu.objects.get_or_create(
        name="View/Track Document Status",
        defaults={
            'application': app,
            'path': "/document-management/status",
            'order': 2,
            'parent': doc_management
        }
    )
    
    approve_doc, _ = Menu.objects.get_or_create(
        name="Approve/Reject Document",
        defaults={
            'application': app,
            'path': "/document-management/approve",
            'order': 3,
            'parent': doc_management
        }
    )
    
    annotate_doc, _ = Menu.objects.get_or_create(
        name="Annotate/Comment on Document",
        defaults={
            'application': app,
            'path': "/document-management/annotate",
            'order': 4,
            'parent': doc_management
        }
    )
    
    delete_doc, _ = Menu.objects.get_or_create(
        name="Delete Document",
        defaults={
            'application': app,
            'path': "/document-management/delete",
            'order': 5,
            'parent': doc_management
        }
    )
    
    # Level 2 Menus - Support
    submit_ticket, _ = Menu.objects.get_or_create(
        name="Submit Support Ticket",
        defaults={
            'application': app,
            'path': "/support/submit",
            'order': 1,
            'parent': support
        }
    )
    
    track_ticket, _ = Menu.objects.get_or_create(
        name="Track Support Ticket Status",
        defaults={
            'application': app,
            'path': "/support/track",
            'order': 2,
            'parent': support
        }
    )

    # Level 2 Menus - Finance
    accounting, _ = Menu.objects.get_or_create(
        name="Accounting",
        defaults={
            'application': app,
            'path': "/accounting",
            'order': 1,
            'parent': finance
        }
    )

    # Assign Menus to Roles
    
    # CEO has access to everything
    all_menus = Menu.objects.all()
    for menu in all_menus:
        MenuRole.objects.get_or_create(
            menu=menu,
            role=ceo_role,
            defaults={
                'can_view': True,
                'can_edit': True,
                'can_delete': True
            }
        )
    
    # CTO has access to most things except some compliance and user management
    cto_menus = [
        dashboard, doc_management, ai_analytics, support,
        upload_doc, view_doc, approve_doc, annotate_doc, delete_doc,
        submit_ticket, track_ticket, finance, accounting
    ]
    
    for menu in cto_menus:
        MenuRole.objects.get_or_create(
            menu=menu,
            role=cto_role,
            defaults={
                'can_view': True,
                'can_edit': True,
                'can_delete': menu not in [delete_doc]  # CTO can't delete documents
            }
        )
    
    # Employee has limited access
    employee_menus = [
        dashboard, doc_management, support,
        upload_doc, view_doc,  # Can't approve/reject, annotate or delete
        submit_ticket, track_ticket
    ]
    
    for menu in employee_menus:
        MenuRole.objects.get_or_create(
            menu=menu,
            role=employee_role,
            defaults={
                'can_view': True,
                'can_edit': False,
                'can_delete': False
            }
        )
    
    print("Sample data created successfully!")

class Command(BaseCommand):
    help = 'Creates sample roles, users, and menu structure'

    def handle(self, *args, **options):
        create_sample_data()
        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))