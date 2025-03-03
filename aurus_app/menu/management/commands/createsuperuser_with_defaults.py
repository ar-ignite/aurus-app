# Create a file in your_app/management/commands/createsuperuser_with_defaults.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from menu.models import Client, Application  # Update with your actual app name

class Command(BaseCommand):
    help = 'Create a superuser with default client and application'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--client-id', required=False)
        parser.add_argument('--application-id', required=False)

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password']
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User with username "{username}" already exists'))
            return
        
        # Get or create default client and application
        client_id = options.get('client_id')
        application_id = options.get('application_id')
        
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Client with ID {client_id} does not exist'))
                return
        else:
            client, created = Client.objects.get_or_create(
                name="Default Client",
                defaults={"name": "Default Client"}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created default client (ID: {client.id})'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Using existing default client (ID: {client.id})'))
        
        if application_id:
            try:
                application = Application.objects.get(id=application_id)
            except Application.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Application with ID {application_id} does not exist'))
                return
        else:
            application, created = Application.objects.get_or_create(
                name="Default Application",
                defaults={"name": "Default Application"}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created default application (ID: {application.id})'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Using existing default application (ID: {application.id})'))
        
        # Create the superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            client=client,
            application=application
        )
        
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully'))