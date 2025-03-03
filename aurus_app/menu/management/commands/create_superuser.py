# create_superuser.py
# A Django management command to create a superuser with application and client ID specified

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import uuid
from menu.models import Application, Client

class Command(BaseCommand):
    help = 'Create a superuser with specified application and client IDs'

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument('--username', required=True, help='Username for the superuser')
        parser.add_argument('--email', required=True, help='Email for the superuser')
        parser.add_argument('--password', required=True, help='Password for the superuser')
        
        # Optional arguments
        parser.add_argument('--first-name', help='First name for the superuser')
        parser.add_argument('--last-name', help='Last name for the superuser')
        parser.add_argument('--application-id', help='UUID of the application to associate with the user')
        parser.add_argument('--client-id', help='UUID of the client to associate with the user')
        parser.add_argument('--create-defaults', action='store_true', help='Create default application and client if not provided')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        application_id = options.get('application_id')
        client_id = options.get('client_id')
        create_defaults = options.get('create_defaults', False)
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User with username "{username}" already exists'))
            return
        
        try:
            with transaction.atomic():
                # Get or create application
                application = None
                client = None
                
                if application_id:
                    try:
                        application = Application.objects.get(id=application_id)
                        self.stdout.write(self.style.SUCCESS(f'Using application: {application.name} (ID: {application.id})'))
                    except Application.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'Application with ID {application_id} does not exist'))
                        if not create_defaults:
                            return
                
                if client_id:
                    try:
                        client = Client.objects.get(id=client_id)
                        self.stdout.write(self.style.SUCCESS(f'Using client: {client.legal_name} (ID: {client.id})'))
                    except Client.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'Client with ID {client_id} does not exist'))
                        if not create_defaults:
                            return
                
                # Create default application and client if needed
                if (not application or not client) and create_defaults:
                    if not application:
                        application, created = Application.objects.get_or_create(
                            name="Default Application",
                            defaults={
                                "description": "Default application created during superuser setup",
                                "version": "1.0.0"
                            }
                        )
                        action = "Created" if created else "Using existing"
                        self.stdout.write(self.style.SUCCESS(f'{action} default application: {application.name} (ID: {application.id})'))
                    
                    if not client:
                        client, created = Client.objects.get_or_create(
                            application=application,
                            legal_name="Default Client",
                            defaults={
                                "short_name": "Default",
                                "legal_structure": "Corporation",
                                "status": "Active",
                                "email": "default@example.com"
                            }
                        )
                        action = "Created" if created else "Using existing"
                        self.stdout.write(self.style.SUCCESS(f'{action} default client: {client.legal_name} (ID: {client.id})'))
                
                # Final check that we have both application and client
                if not application or not client:
                    self.stdout.write(self.style.ERROR('Cannot create superuser without both application and client'))
                    return
                
                # Create the superuser
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    application=application,
                    client=client,
                    is_staff=True,
                    is_superuser=True
                )
                
                self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {username}'))
                self.stdout.write(self.style.SUCCESS(f'Application: {application.name} (ID: {application.id})'))
                self.stdout.write(self.style.SUCCESS(f'Client: {client.legal_name} (ID: {client.id})'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))