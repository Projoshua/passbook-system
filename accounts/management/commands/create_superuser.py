# accounts/management/commands/create_superuser.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser with sysadmin access'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Superuser username')
        parser.add_argument('--email', type=str, help='Superuser email')
        parser.add_argument('--password', type=str, help='Superuser password')

    def handle(self, *args, **options):
        username = options.get('username') or input('Username: ')
        email = options.get('email') or input('Email: ')
        password = options.get('password') or input('Password: ')

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User {username} already exists')
            )
            return

        # First create the superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        # Then update the user_type separately
        user.user_type = 'sysadmin'
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser: {username} with sysadmin access')
        )
