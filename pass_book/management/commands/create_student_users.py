"""
Django management command to create user accounts for students that don't have them.

This command finds all students without user accounts and creates user accounts
for them using the same logic as the Student model's create_user_account() method.

Usage:
    python manage.py create_student_users
    
    # Dry run (show what would be created without actually creating)
    python manage.py create_student_users --dry-run
    
    # Limit number of students to process
    python manage.py create_student_users --limit 100
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from pass_book.models import Student

User = get_user_model()


class Command(BaseCommand):
    help = 'Create user accounts for students that do not have user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating users',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of students to process',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='123',
            help='Default password for created user accounts (default: 123)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options.get('limit')
        default_password = options.get('password', '123')

        # Find students without user accounts
        students_without_users = Student.objects.filter(user__isnull=True)
        
        # Also check for students with static_access_number (required for username)
        students_without_users = students_without_users.exclude(
            static_access_number__isnull=True
        ).exclude(
            static_access_number=''
        )

        total_count = students_without_users.count()
        
        if limit:
            students_without_users = students_without_users[:limit]
            actual_count = students_without_users.count()
        else:
            actual_count = total_count

        if actual_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No students found without user accounts.')
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f'Found {actual_count} student(s) without user accounts'
                + (f' (showing {actual_count} of {total_count} total)' if limit and total_count > limit else '')
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n=== DRY RUN MODE - No users will be created ===\n')
            )

        created_count = 0
        skipped_count = 0
        error_count = 0

        for student in students_without_users:
            try:
                # Ensure student has static_access_number
                if not student.static_access_number:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping {student.name} (ID: {student.id}): No static_access_number'
                        )
                    )
                    skipped_count += 1
                    continue

                # Check if user already exists with this username
                if User.objects.filter(username=student.static_access_number).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping {student.name} ({student.static_access_number}): '
                            f'User with this username already exists'
                        )
                    )
                    skipped_count += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        f'Would create user for: {student.name} '
                        f'({student.static_access_number})'
                    )
                    created_count += 1
                else:
                    # Create user account
                    with transaction.atomic():
                        # Split name for first_name and last_name
                        name_parts = student.name.split()
                        first_name = name_parts[0] if name_parts else ''
                        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

                        user = User.objects.create_user(
                            username=student.static_access_number,
                            password=default_password,
                            user_type='student',
                            first_name=first_name,
                            last_name=last_name,
                            email=f'{student.static_access_number}@slau.ac.ug',
                        )
                        user.is_active = True
                        user.save()

                        # Link the user to the student
                        student.user = user
                        student.save(update_fields=['user'])

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Created user account for {student.name}: '
                                f'{student.static_access_number}'
                            )
                        )
                        created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error creating user for {student.name} '
                        f'({student.static_access_number}): {str(e)}'
                    )
                )
                error_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN SUMMARY:'))
        else:
            self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Errors: {error_count}')
        self.stdout.write(f'  Total processed: {created_count + skipped_count + error_count}')
        self.stdout.write('=' * 60)

