# management/commands/populate_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction
from menu.models import (
    Application, Client, Role, CustomUser, Menu, MenuRole, 
    FundingInstitution, DocumentCategory, DocumentType, LoanApplication
)
import uuid
from django.utils.timezone import now
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Populates the database with initial users, roles, menus, and other data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data population...')
        
        try:
            with transaction.atomic():
                # Create application
                app, _ = Application.objects.get_or_create(
                    name="Mortgage Document System",
                    defaults={
                        "description": "Mortgage document processing system",
                        "version": "1.0.0"
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'Application created: {app.name}'))
                
                # Create client
                client, _ = Client.objects.get_or_create(
                    legal_name="Acme Mortgage Corporation",
                    defaults={
                        "application": app,
                        "short_name": "AcmeMort",
                        "legal_structure": "Corporation",
                        "fein": "12-3456789",
                        "address": "123 Main St",
                        "city": "Anytown",
                        "state": "CA",
                        "zip_code": "90210",
                        "country": "USA",
                        "email": "info@acmemortgage.com",
                        "website": "https://www.acmemortgage.com",
                        "industry": "Financial Services",
                        "status": "Active"
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'Client created: {client.legal_name}'))
                
                # Create roles and groups
                self._create_role_and_group("CEO", "Chief Executive Officer", app)
                self._create_role_and_group("CTO", "Chief Technology Officer", app)
                self._create_role_and_group("Loan Applicant", "Mortgage Loan Applicant", app)
                self._create_role_and_group("Loan Officer", "Mortgage Loan Officer", app)
                self._create_role_and_group("Admin", "System Administrator", app)
                
                # Create funding institutions
                institutions = [
                    {"name": "First Mortgage Bank", "code": "FMB"}
                    # {"name": "Home Loan Partners", "code": "HLP"},
                    # {"name": "Capital Funding Group", "code": "CFG"},
                    # {"name": "Secure Mortgage Inc", "code": "SMI"}
                ]
                created_institutions = []
                FundingInstitution.objects.all().delete()
                for inst_data in institutions:
                    institution, created = FundingInstitution.objects.get_or_create(
                        code=inst_data["code"],
                        defaults={"name": inst_data["name"]}
                    )
                    created_institutions.append(institution)
                    self.stdout.write(self.style.SUCCESS(f'Institution created: {institution.name}'))
                
                # Create users
                self._create_user("uday", "Uday", "Kumar", "CEO", app, client, created_institutions[0])
                self._create_user("aniruddha", "Aniruddha", "Laha", "CTO", app, client, created_institutions[0])
                self._create_user("johndoe", "John", "Doe", "Loan Applicant", app, client, created_institutions[0])
                self._create_user("sarahsmith", "Sarah", "Smith", "Loan Officer", app, client, created_institutions[0])
                self._create_user("admin", "Admin", "User", "Admin", app, client, created_institutions[0])
                
                # Create document categories
                self._create_document_categories(app)
                
                # Create menu structure for each institution
                for institution in created_institutions:
                    self._create_menus_for_institution(app, institution)
                
                # Create sample loan applications for John Doe (Loan Applicant)
                loan_applicant = CustomUser.objects.get(username="johndoe")
                self._create_sample_loan_applications(app, client, loan_applicant)
                
                self.stdout.write(self.style.SUCCESS('Data population completed successfully!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during data population: {str(e)}'))
            raise
    
    def _create_role_and_group(self, name, description, app):
        """Create a role and its associated group"""
        group, _ = Group.objects.get_or_create(name=name)
        role, created = Role.objects.get_or_create(
            name=name,
            defaults={
                "group": group,
                "description": description,
                "application": app
            }
        )
        if not created:
            # Update the role if it already exists
            role.group = group
            role.description = description
            role.application = app
            role.save()
        
        self.stdout.write(self.style.SUCCESS(f'Role created: {role.name}'))
        return role
    
    def _create_user(self, username, first_name, last_name, role_name, app, client, selected_institution):
        """Create a user with the specified role"""
        # Get role
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Role not found: {role_name}'))
            return None
        
        # Create or update user
        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{username}@example.com",
                "client": client,
                "application": app,
                "role": role,
                "selected_institution": selected_institution,
                "is_active": True,
            }
        )
        
        if created:
            # Set password for new user
            user.set_password("password123")
            user.save()
            
            # Add to group
            user.groups.add(role.group)
            
            self.stdout.write(self.style.SUCCESS(f'User created: {user.username} ({role_name})'))
        else:
            # Update existing user
            user.first_name = first_name
            user.last_name = last_name
            user.email = f"{username}@example.com"
            user.client = client
            user.application = app
            user.role = role
            user.selected_institution = selected_institution
            user.save()
            
            # Update group membership
            user.groups.clear()
            user.groups.add(role.group)
            
            self.stdout.write(self.style.SUCCESS(f'User updated: {user.username} ({role_name})'))
        
        return user
    
    def _create_document_categories(self, app):
        """Create document categories"""
        categories = [
            ('identification', 'Identification Documents', 'Government-issued ID, SSN, etc.'),
            ('income', 'Income Verification', 'Pay stubs, W-2s, tax returns, etc.'),
            ('asset', 'Asset Documentation', 'Bank statements, investment accounts, etc.'),
            ('credit', 'Credit History', 'Credit reports, credit score, etc.'),
            ('property', 'Property Information', 'Property details, appraisal, etc.'),
            ('debt', 'Debt Obligations', 'Existing loans, credit card debt, etc.'),
            ('down_payment', 'Down Payment Verification', 'Proof of down payment funds'),
            ('loan_specific', 'Loan-Specific Requirements', 'Specific documents for the loan'),
            ('additional', 'Additional Documentation', 'Other supporting documents'),
            ('untagged', 'Untagged', 'Documents not yet categorized')
        ]
        
        for index, (code, name, description) in enumerate(categories):
            category, created = DocumentCategory.objects.get_or_create(
                category_code=code,
                application=app,
                defaults={
                    "category_name": name,
                    "description": description,
                    "category_seq": str(index + 1),
                    "order": index
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Document category created: {category.category_name}'))
            else:
                # Update if it exists
                category.category_name = name
                category.description = description
                category.category_seq = str(index + 1)
                category.order = index
                category.save()
                self.stdout.write(self.style.SUCCESS(f'Document category updated: {category.category_name}'))
                
            # Create document types for each category
            self._create_document_types(app, category)
    
    def _create_document_types(self, app, category):
        """Create document types for a category"""
        document_types = {
            'identification': [
                ('Drivers License', 'State-issued driver\'s license', True),
                ('Passport', 'Government-issued passport', True),
                ('Social Security Card', 'Social Security Number card', True),
                ('Birth Certificate', 'Official birth certificate', False)
            ],
            'income': [
                ('Pay Stubs', 'Recent pay stubs (last 30 days)', True),
                ('W-2 Forms', 'W-2 forms for last 2 years', True),
                ('Tax Returns', 'Federal tax returns for last 2 years', True),
                ('Employment Verification', 'Verification of employment letter', False)
            ],
            'asset': [
                ('Bank Statements', 'Bank statements for last 2-3 months', True),
                ('Investment Accounts', 'Investment account statements', False),
                ('Retirement Accounts', '401(k) or IRA statements', False)
            ],
            'credit': [
                ('Credit Report', 'Recent credit report', True),
                ('Credit Score', 'Credit score documentation', True),
                ('Credit History', 'Credit history documentation', False)
            ],
            'property': [
                ('Property Appraisal', 'Professional property appraisal', True),
                ('Home Inspection', 'Home inspection report', False),
                ('Property Tax Statement', 'Current property tax statement', True)
            ]
        }
        
        # Get types for this category
        types = document_types.get(category.category_code, [])
        
        for index, (name, description, required) in enumerate(types):
            doc_type, created = DocumentType.objects.get_or_create(
                type_name=name,
                category=category,
                application=app,
                defaults={
                    "description": description,
                    "is_required": required
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Document type created: {doc_type.type_name}'))
            else:
                # Update if it exists
                doc_type.description = description
                doc_type.is_required = required
                doc_type.save()
                self.stdout.write(self.style.SUCCESS(f'Document type updated: {doc_type.type_name}'))
    
    def _create_menus_for_institution(self, app, institution):
        """Create menu structure for an institution"""
        # Get roles
        ceo_role = Role.objects.get(name="CEO")
        cto_role = Role.objects.get(name="CTO")
        applicant_role = Role.objects.get(name="Loan Applicant")
        officer_role = Role.objects.get(name="Loan Officer")
        admin_role = Role.objects.get(name="Admin")
        
        # Create top-level menus
        dashboard, _ = Menu.objects.get_or_create(
            name="Dashboard",
            application=app,
            funding_institution=institution,
            defaults={
                'path': "/dashboard",
                'order': 1
            }
        )
        
        doc_management, _ = Menu.objects.get_or_create(
            name="Document Management",
            application=app,
            funding_institution=institution,
            defaults={
                'path': "/document-management",
                'order': 2
            }
        )
        
        analytics, _ = Menu.objects.get_or_create(
            name="AI & Analytics",
            application=app,
            funding_institution=institution,
            defaults={
                'path': "/analytics",
                'order': 3
            }
        )
        
        compliance, _ = Menu.objects.get_or_create(
            name="Compliance",
            application=app,
            funding_institution=institution,
            defaults={
                'path': "/compliance",
                'order': 4
            }
        )
        
        user_management, _ = Menu.objects.get_or_create(
            name="User Management",
            application=app,
            funding_institution=institution,
            defaults={
                'path': "/user-management",
                'order': 5
            }
        )
        
        support, _ = Menu.objects.get_or_create(
            name="Support",
            application=app,
            funding_institution=institution,
            defaults={
                'path': "/support",
                'order': 6
            }
        )
        
        # Create submenus for Document Management
        upload_doc, _ = Menu.objects.get_or_create(
            name="Upload Document",
            application=app,
            funding_institution=institution,
            parent=doc_management,
            defaults={
                'path': "/document-management/upload",
                'order': 1
            }
        )
        
        view_doc, _ = Menu.objects.get_or_create(
            name="View/Track Document Status",
            application=app,
            funding_institution=institution,
            parent=doc_management,
            defaults={
                'path': "/document-management/status",
                'order': 2
            }
        )
        
        approve_doc, _ = Menu.objects.get_or_create(
            name="Approve/Reject Document",
            application=app,
            funding_institution=institution,
            parent=doc_management,
            defaults={
                'path': "/document-management/approve",
                'order': 3
            }
        )
        
        annotate_doc, _ = Menu.objects.get_or_create(
            name="Annotate/Comment on Document",
            application=app,
            funding_institution=institution,
            parent=doc_management,
            defaults={
                'path': "/document-management/annotate",
                'order': 4
            }
        )
        
        delete_doc, _ = Menu.objects.get_or_create(
            name="Delete Document",
            application=app,
            funding_institution=institution,
            parent=doc_management,
            defaults={
                'path': "/document-management/delete",
                'order': 5
            }
        )
        
        # Create submenus for Support
        submit_ticket, _ = Menu.objects.get_or_create(
            name="Submit Support Ticket",
            application=app,
            funding_institution=institution,
            parent=support,
            defaults={
                'path': "/support/submit",
                'order': 1
            }
        )
        
        track_ticket, _ = Menu.objects.get_or_create(
            name="Track Support Ticket Status",
            application=app,
            funding_institution=institution,
            parent=support,
            defaults={
                'path': "/support/track",
                'order': 2
            }
        )
        
        # Assign all menus to CEO role
        all_menus = Menu.objects.filter(funding_institution=institution)
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
            
            # Also assign to admin role
            MenuRole.objects.get_or_create(
                menu=menu,
                role=admin_role,
                defaults={
                    'can_view': True,
                    'can_edit': True,
                    'can_delete': True
                }
            )
        
        # Assign CTO menus
        cto_menus = [
            dashboard, doc_management, analytics, support,
            upload_doc, view_doc, approve_doc, annotate_doc, delete_doc,
            submit_ticket, track_ticket
        ]
        
        for menu in cto_menus:
            MenuRole.objects.get_or_create(
                menu=menu,
                role=cto_role,
                defaults={
                    'can_view': True,
                    'can_edit': True,
                    'can_delete': menu not in [delete_doc]
                }
            )
        
        # Assign Loan Applicant menus
        applicant_menus = [
            dashboard, doc_management, support,
            upload_doc, view_doc,
            submit_ticket, track_ticket
        ]
        
        for menu in applicant_menus:
            MenuRole.objects.get_or_create(
                menu=menu,
                role=applicant_role,
                defaults={
                    'can_view': True,
                    'can_edit': False,
                    'can_delete': False
                }
            )
            
        # Assign Loan Officer menus
        officer_menus = [
            dashboard, doc_management, analytics, support,
            upload_doc, view_doc, approve_doc, annotate_doc,
            submit_ticket, track_ticket
        ]
        
        for menu in officer_menus:
            MenuRole.objects.get_or_create(
                menu=menu,
                role=officer_role,
                defaults={
                    'can_view': True,
                    'can_edit': True,
                    'can_delete': False
                }
            )
    
    def _create_sample_loan_applications(self, app, client, user):
        """Create sample loan applications for a user"""
        # Create 3 loan applications with different statuses
        loan_data = [
            {
                "loan_amount": 250000,
                "loan_purpose": "Home Purchase",
                "loan_term": 30,
                "interest_rate": 3.75,
                "application_status": "APPROVED",
                "applicant_name": f"{user.first_name} {user.last_name}",
                "credit_score": 760,
                "dti_ratio": 48,
                "case_readiness": 60,
                "document_index": 85
            },
            {
                "loan_amount": 180000,
                "loan_purpose": "Refinance",
                "loan_term": 15,
                "interest_rate": 3.25,
                "application_status": "UNDER_REVIEW",
                "applicant_name": f"{user.first_name} {user.last_name}",
                "credit_score": 720,
                "dti_ratio": 42,
                "case_readiness": 45,
                "document_index": 60
            },
            {
                "loan_amount": 320000,
                "loan_purpose": "Home Improvement",
                "loan_term": 20,
                "interest_rate": 4.0,
                "application_status": "DRAFT",
                "applicant_name": f"{user.first_name} {user.last_name}",
                "credit_score": 680,
                "dti_ratio": 52,
                "case_readiness": 25,
                "document_index": 30
            }
        ]
        
        created_loans = []
        for index, data in enumerate(loan_data):
            # Add rate expiry date and submission date based on status
            if data["application_status"] == "APPROVED":
                rate_expiry = now() + timedelta(days=60)
                submission_date = now() - timedelta(days=30)
                decision_date = now() - timedelta(days=10)
            elif data["application_status"] == "UNDER_REVIEW":
                rate_expiry = now() + timedelta(days=30)
                submission_date = now() - timedelta(days=15)
                decision_date = None
            else:
                rate_expiry = now() + timedelta(days=14)
                submission_date = None
                decision_date = None
            
            loan, created = LoanApplication.objects.get_or_create(
                user=user,
                client=client,
                application=app,
                loan_amount=data["loan_amount"],
                defaults={
                    "loan_purpose": data["loan_purpose"],
                    "loan_term": data["loan_term"],
                    "interest_rate": data["interest_rate"],
                    "rate_expiry_date": rate_expiry,
                    "application_status": data["application_status"],
                    "submission_date": submission_date,
                    "decision_date": decision_date,
                    "applicant_name": data["applicant_name"],
                    "credit_score": data["credit_score"],
                    "dti_ratio": data["dti_ratio"],
                    "case_readiness": data["case_readiness"],
                    "document_index": data["document_index"]
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Loan application created: ${data["loan_amount"]:,} for {data["loan_purpose"]}'))
            else:
                # Update if it exists
                for field, value in data.items():
                    setattr(loan, field, value)
                loan.rate_expiry_date = rate_expiry
                loan.submission_date = submission_date
                loan.decision_date = decision_date
                loan.save()
                self.stdout.write(self.style.SUCCESS(f'Loan application updated: ${data["loan_amount"]:,} for {data["loan_purpose"]}'))
            
            created_loans.append(loan)
        
        return created_loans