#!/usr/bin/env python
"""
Standalone script to create user accounts for students without user accounts.

This script can be run in the Django shell or as a standalone script.

Usage in Django shell:
    python manage.py shell < create_student_users_script.py

Or run directly (if Django is set up):
    python create_student_users_script.py

Or copy and paste the code into Django shell:
    python manage.py shell
    # Then paste the code below
"""

import os
import sys
import django

# Setup Django environment
if __name__ == '__main__':
    # Get the directory containing this script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, BASE_DIR)
    
    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AttendanceSystem.settings')
    
    # Setup Django
    django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from pass_book.models import Student

User = get_user_model()


def create_student_users(dry_run=False, limit=None, default_password='123'):
    """
    Create user accounts for students that do not have user accounts.
    
    Args:
        dry_run (bool): If True, only show what would be created without creating
        limit (int): Limit the number of students to process (None for all)
        default_password (str): Default password for created user accounts
    
    Returns:
        dict: Summary with counts of created, skipped, and errors
    """
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
        print('✓ No students found without user accounts.')
        return {
            'created': 0,
            'skipped': 0,
            'errors': 0,
            'total': 0
        }

    print(f'Found {actual_count} student(s) without user accounts'
          + (f' (showing {actual_count} of {total_count} total)' if limit and total_count > limit else ''))
    print()

    if dry_run:
        print('=== DRY RUN MODE - No users will be created ===\n')

    created_count = 0
    skipped_count = 0
    error_count = 0

    for student in students_without_users:
        try:
            # Ensure student has static_access_number
            if not student.static_access_number:
                print(f'⚠ Skipping {student.name} (ID: {student.id}): No static_access_number')
                skipped_count += 1
                continue

            # Check if user already exists with this username
            if User.objects.filter(username=student.static_access_number).exists():
                print(f'⚠ Skipping {student.name} ({student.static_access_number}): '
                      f'User with this username already exists')
                skipped_count += 1
                continue

            if dry_run:
                print(f'Would create user for: {student.name} ({student.static_access_number})')
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

                    print(f'✓ Created user account for {student.name}: {student.static_access_number}')
                    created_count += 1

        except Exception as e:
            print(f'✗ Error creating user for {student.name} ({student.static_access_number}): {str(e)}')
            error_count += 1

    # Summary
    print()
    print('=' * 60)
    if dry_run:
        print('DRY RUN SUMMARY:')
    else:
        print('SUMMARY:')
    print(f'  Created: {created_count}')
    print(f'  Skipped: {skipped_count}')
    print(f'  Errors: {error_count}')
    print(f'  Total processed: {created_count + skipped_count + error_count}')
    print('=' * 60)

    return {
        'created': created_count,
        'skipped': skipped_count,
        'errors': error_count,
        'total': created_count + skipped_count + error_count
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Create user accounts for students without user accounts'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without actually creating users'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit the number of students to process'
    )
    parser.add_argument(
        '--password',
        type=str,
        default='123',
        help='Default password for created user accounts (default: 123)'
    )

    args = parser.parse_args()

    create_student_users(
        dry_run=args.dry_run,
        limit=args.limit,
        default_password=args.password
    )

