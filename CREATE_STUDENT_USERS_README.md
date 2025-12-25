# Create Student User Accounts

This document explains how to create user accounts for students that were imported but don't have user accounts yet.

## Overview

When students are imported into the system, they may not have user accounts created automatically. This guide provides two methods to create user accounts for these students:

1. **Django Management Command** (Recommended)
2. **Standalone Python Script**

Both methods will:
- Find all students without user accounts
- Create user accounts with:
  - Username: `static_access_number`
  - Password: `123` (default, can be changed)
  - User type: `student`
  - Email: `{static_access_number}@slau.ac.ug`
- Link the user account to the student record

## Prerequisites

- Access to the Django web container
- Students must have a `static_access_number` (required for username)

## Method 1: Django Management Command (Recommended)

### Basic Usage

```bash
# Run inside Django web container
python manage.py create_student_users
```

### Options

```bash
# Dry run (see what would be created without actually creating)
python manage.py create_student_users --dry-run

# Limit number of students to process
python manage.py create_student_users --limit 100

# Use custom password instead of default '123'
python manage.py create_student_users --password mypassword

# Combine options
python manage.py create_student_users --dry-run --limit 50
```

### Docker Container Usage

If you're using Docker, run:

```bash
# Find your Django container name
docker ps

# Execute the command in the container
docker exec -it <container_name> python manage.py create_student_users

# Or if using docker-compose
docker-compose exec web python manage.py create_student_users
```

## Method 2: Standalone Python Script

### Option A: Run as Script

```bash
# Run directly (if Django environment is set up)
python create_student_users_script.py

# With options
python create_student_users_script.py --dry-run
python create_student_users_script.py --limit 100
python create_student_users_script.py --password mypassword
```

### Option B: Run in Django Shell

```bash
# Open Django shell
python manage.py shell

# Then copy and paste the code from create_student_users_script.py
# Or import and run the function:
from create_student_users_script import create_student_users
create_student_users()
```

### Option C: Pipe Script to Shell

```bash
python manage.py shell < create_student_users_script.py
```

## Docker Container Shell Commands

### Quick Commands for Docker

```bash
# Method 1: Management Command
docker-compose exec web python manage.py create_student_users

# Method 2: Standalone Script (copy script into container first)
docker cp create_student_users_script.py <container_name>:/app/
docker exec -it <container_name> python create_student_users_script.py

# Method 3: Django Shell with script
docker cp create_student_users_script.py <container_name>:/app/
docker exec -it <container_name> python manage.py shell < create_student_users_script.py
```

## What Gets Created

For each student without a user account, the script will:

1. **Check prerequisites:**
   - Student must have a `static_access_number`
   - No existing user with the same username

2. **Create user account:**
   - Username: Student's `static_access_number`
   - Password: `123` (default, can be customized)
   - User type: `student`
   - First name: First word of student's name
   - Last name: Remaining words of student's name
   - Email: `{static_access_number}@slau.ac.ug`
   - Active: `True`

3. **Link accounts:**
   - Link the user account to the student record via `student.user`

## Output Example

```
Found 25 student(s) without user accounts

✓ Created user account for John Doe: BAGC-AA01
✓ Created user account for Jane Smith: BAGC-AA02
⚠ Skipping Bob Johnson (BAGC-AA03): User with this username already exists
...

============================================================
SUMMARY:
  Created: 23
  Skipped: 2
  Errors: 0
  Total processed: 25
============================================================
```

## Troubleshooting

### Error: "No students found without user accounts"
- All students already have user accounts, or
- Students don't have `static_access_number` set

### Error: "User with this username already exists"
- A user account already exists with that `static_access_number` as username
- The script will skip these students

### Error: "No static_access_number"
- Student records need to have `static_access_number` generated first
- The Student model should auto-generate this on save

## Notes

- The script uses database transactions to ensure data consistency
- Students are processed one at a time to avoid bulk operation issues
- The default password is `123` - students should change this on first login
- Email addresses are placeholder format and can be updated later

