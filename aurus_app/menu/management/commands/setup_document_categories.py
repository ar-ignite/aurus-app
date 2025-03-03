# management/commands/setup_document_categories.py
from django.core.management.base import BaseCommand
from django.db import transaction
import uuid
from menu.models import Application, DocumentCategory, DocumentType

class Command(BaseCommand):
    help = 'Set up initial document categories and types for an application'

    def add_arguments(self, parser):
        parser.add_argument('--application-id', required=True, help='UUID of the application')
        parser.add_argument('--force', action='store_true', help='Force recreation of categories even if they exist')

    def handle(self, *args, **options):
        application_id = options['application_id']
        force = options.get('force', False)
        
        try:
            application = Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Application with ID {application_id} does not exist'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Setting up document categories for application: {application.name}'))
        
        # Define the categories and their document types
        categories_data = [
            {
                'code': 'identification',
                'name': 'Identification Documents',
                'description': 'Government-issued ID, SSN, etc.',
                'types': [
                    {
                        'name': 'Driver\'s License',
                        'description': 'State-issued driver\'s license',
                        'required': True
                    },
                    {
                        'name': 'Passport',
                        'description': 'Government-issued passport',
                        'required': False
                    },
                    {
                        'name': 'Social Security Card',
                        'description': 'Social Security Number card',
                        'required': True
                    },
                    {
                        'name': 'Proof of Legal Residency',
                        'description': 'For non-citizens',
                        'required': False
                    }
                ]
            },
            {
                'code': 'income',
                'name': 'Income Verification',
                'description': 'Pay stubs, W-2s, tax returns, etc.',
                'types': [
                    {
                        'name': 'Pay Stubs',
                        'description': 'Recent pay stubs (last 30 days)',
                        'required': True
                    },
                    {
                        'name': 'W-2 Forms',
                        'description': 'W-2 forms for last 2 years',
                        'required': True
                    },
                    {
                        'name': 'Tax Returns',
                        'description': 'Federal tax returns for last 2 years',
                        'required': True
                    },
                    {
                        'name': 'Employment Verification',
                        'description': 'Verification of employment letter',
                        'required': False
                    }
                ]
            },
            {
                'code': 'asset',
                'name': 'Asset Documentation',
                'description': 'Bank statements, investment accounts, etc.',
                'types': [
                    {
                        'name': 'Bank Statements',
                        'description': 'Bank statements for last 2-3 months',
                        'required': True
                    },
                    {
                        'name': 'Investment Accounts',
                        'description': 'Investment account statements',
                        'required': False
                    },
                    {
                        'name': 'Retirement Accounts',
                        'description': '401(k) or IRA statements',
                        'required': False
                    }
                ]
            },
            {
                'code': 'credit',
                'name': 'Credit History',
                'description': 'Credit reports, credit score, etc.',
                'types': [
                    {
                        'name': 'Credit Report',
                        'description': 'Recent credit report',
                        'required': True
                    },
                    {
                        'name': 'Credit Score',
                        'description': 'Credit score documentation',
                        'required': False
                    },
                    {
                        'name': 'Credit History',
                        'description': 'Credit history documentation',
                        'required': False
                    }
                ]
            },
            {
                'code': 'property',
                'name': 'Property Information',
                'description': 'Property details, appraisal, etc.',
                'types': [
                    {
                        'name': 'Property Appraisal',
                        'description': 'Professional property appraisal',
                        'required': True
                    },
                    {
                        'name': 'Home Inspection',
                        'description': 'Home inspection report',
                        'required': False
                    },
                    {
                        'name': 'Property Tax Statement',
                        'description': 'Current property tax statement',
                        'required': True
                    },
                    {
                        'name': 'Homeowners Insurance',
                        'description': 'Proof of homeowners insurance',
                        'required': True
                    }
                ]
            },
            {
                'code': 'debt',
                'name': 'Debt Obligations',
                'description': 'Existing loans, credit card debt, etc.',
                'types': [
                    {
                        'name': 'Existing Mortgage Statements',
                        'description': 'Current mortgage statements',
                        'required': False
                    },
                    {
                        'name': 'Auto Loan Statements',
                        'description': 'Current auto loan statements',
                        'required': False
                    },
                    {
                        'name': 'Credit Card Statements',
                        'description': 'Recent credit card statements',
                        'required': False
                    },
                    {
                        'name': 'Student Loan Information',
                        'description': 'Current student loan details',
                        'required': False
                    }
                ]
            },
            {
                'code': 'down_payment',
                'name': 'Down Payment Verification',
                'description': 'Proof of down payment funds',
                'types': [
                    {
                        'name': 'Gift Letter',
                        'description': 'Letter confirming gift funds for down payment',
                        'required': False
                    },
                    {
                        'name': 'Deposit Verification',
                        'description': 'Proof of deposit for down payment',
                        'required': True
                    },
                    {
                        'name': 'Source of Funds',
                        'description': 'Documentation of source of down payment funds',
                        'required': True
                    }
                ]
            },
            {
                'code': 'loan_specific',
                'name': 'Loan-Specific Requirements',
                'description': 'Specific documents for the loan',
                'types': [
                    {
                        'name': 'Loan Application',
                        'description': 'Completed loan application form',
                        'required': True
                    },
                    {
                        'name': 'Rate Lock Agreement',
                        'description': 'Agreement to lock in interest rate',
                        'required': False
                    },
                    {
                        'name': 'Disclosures',
                        'description': 'Signed loan disclosure documents',
                        'required': True
                    }
                ]
            },
            {
                'code': 'additional',
                'name': 'Additional Documentation',
                'description': 'Other supporting documents',
                'types': [
                    {
                        'name': 'Divorce Decree',
                        'description': 'If applicable',
                        'required': False
                    },
                    {
                        'name': 'Bankruptcy Documents',
                        'description': 'If applicable',
                        'required': False
                    },
                    {
                        'name': 'Power of Attorney',
                        'description': 'If applicable',
                        'required': False
                    }
                ]
            },
            {
                'code': 'untagged',
                'name': 'Untagged',
                'description': 'Documents not yet categorized',
                'types': [
                    {
                        'name': 'Unidentified Document',
                        'description': 'Document pending categorization',
                        'required': False
                    }
                ]
            }
        ]
        
        try:
            with transaction.atomic():
                # Create categories and types
                for i, cat_data in enumerate(categories_data):
                    # Check if category exists
                    try:
                        category = DocumentCategory.objects.get(
                            application=application,
                            category_code=cat_data['code']
                        )
                        
                        if force:
                            # Update existing category
                            category.category_name = cat_data['name']
                            category.description = cat_data['description']
                            category.order = i
                            category.category_seq = str((i + 1) * 10)
                            category.save()
                            self.stdout.write(self.style.SUCCESS(f'Updated category: {category.category_name}'))
                        else:
                            self.stdout.write(self.style.SUCCESS(f'Category exists: {category.category_name}'))
                    except DocumentCategory.DoesNotExist:
                        # Create new category
                        category = DocumentCategory.objects.create(
                            application=application,
                            category_code=cat_data['code'],
                            category_name=cat_data['name'],
                            description=cat_data['description'],
                            order=i,
                            category_seq=str((i + 1) * 10)
                        )
                        self.stdout.write(self.style.SUCCESS(f'Created category: {category.category_name}'))
                    
                    # Create or update document types
                    for j, type_data in enumerate(cat_data['types']):
                        try:
                            doc_type = DocumentType.objects.get(
                                application=application,
                                category=category,
                                type_name=type_data['name']
                            )
                            
                            if force:
                                # Update existing type
                                doc_type.description = type_data['description']
                                doc_type.is_required = type_data['required']
                                doc_type.save()
                                self.stdout.write(self.style.SUCCESS(f'  Updated type: {doc_type.type_name}'))
                            else:
                                self.stdout.write(self.style.SUCCESS(f'  Type exists: {doc_type.type_name}'))
                        except DocumentType.DoesNotExist:
                            # Create new type
                            doc_type = DocumentType.objects.create(
                                application=application,
                                category=category,
                                type_name=type_data['name'],
                                description=type_data['description'],
                                is_required=type_data['required']
                            )
                            self.stdout.write(self.style.SUCCESS(f'  Created type: {doc_type.type_name}'))
                
                self.stdout.write(self.style.SUCCESS('Document categories and types setup completed successfully'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up document categories: {str(e)}'))