# accounts/management/commands/create_user.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a regular user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='Username')
        parser.add_argument('--email', type=str, required=True, help='Email')
        parser.add_argument('--password', type=str, required=True, help='Password')
        parser.add_argument('--user_type', type=str, required=True, help='User type')
        parser.add_argument('--phone_number', type=str, help='Phone number (optional)')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        user_type = options['user_type']
        phone_number = options.get('phone_number')

        # Validate user type
        valid_types = [choice[0] for choice in User.USER_TYPE_CHOICES]
        if user_type not in valid_types:
            self.stdout.write(
                self.style.ERROR(f'Invalid user type. Valid options: {valid_types}')
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User {username} already exists')
            )
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type=user_type,
            phone_number=phone_number
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created user: {username} with type: {user_type}')
        )