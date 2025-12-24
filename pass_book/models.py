
from django.db import models

from django.core.validators import MaxValueValidator, MinValueValidator
import uuid
from datetime import datetime
import uuid
from django.db import models
from django.utils.text import slugify
from django.conf import settings
import uuid
from django.db import models, transaction
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
import re

class Program(models.Model):
    """Academic program/degree (e.g., Bachelor of Science in Computer Science)"""
    code = models.CharField(
        max_length=10, 
        unique=True, 
        help_text="Program code (e.g., BSCS)"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(help_text="Duration in years")
    faculty = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

# models.py




'''
class Student(models.Model):
    SESSION_CHOICES = [
        ('D', 'Day'),
        ('E', 'Evening'),
        ('W', 'Weekend'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic student information
    student_photo = models.ImageField(
        upload_to='student_photos/',
        blank=True,
        null=True,
        help_text="Upload a clear face photo of the student"
        )
    parent_guardian_photo = models.ImageField(
        upload_to='parent_photos/',
        blank=True,
        null=True,
        help_text="Upload a clear face photo of the parent or guardian"
        )
    name = models.CharField(max_length=200)
    program = models.ForeignKey(
        'Program',
        on_delete=models.PROTECT,
        related_name='students'
    )
    nationality = models.CharField(max_length=100)
    student_contact = models.CharField(max_length=20)
    parent_guardian_name = models.CharField(max_length=200, blank=True, null=True)
    parent_guardian_contact = models.CharField(max_length=20, blank=True, null=True)
    parent_guardian_signature = models.ImageField(upload_to='parent_signatures/', blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Academic & Session Info
    admission_year = models.PositiveIntegerField(help_text="Year of admission (e.g., 2024)")
    session = models.CharField(max_length=1, choices=SESSION_CHOICES, help_text="Study session")
    expected_graduation_year = models.IntegerField(blank=True, null=True)
    
    # Manual Receipt
    manual_received = models.BooleanField(default=False)
    manual_received_date = models.DateField(blank=True, null=True)
    
    # Generated Fields (immutable after creation)
    registration_number = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Manual registration number (e.g., 909/24D/U/A001)"
    )
    program_code = models.CharField(max_length=10, blank=True, help_text="Copied from Program.code")
    student_number = models.CharField(max_length=10, blank=True, help_text="Sequential code like AA01")
    
    # NEW: Static access number field
    static_access_number = models.CharField(
        max_length=15, 
        unique=True, 
        blank=True, 
        help_text="Format: COURSE-XXXX (e.g., BAGC-AA01)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True,
        help_text="Linked user account for this student"
    )
    
    def save(self, *args, **kwargs):
        # Generate static access number if not exists
        if not self.static_access_number:
            self.static_access_number = self.generate_static_access_number()
        
        # Copy program code if not set
        if not self.program_code and self.program:
            self.program_code = self.program.code
            
        super().save(*args, **kwargs)
    
    def generate_static_access_number(self):
        """
        Generate static access number in format: PROGRAM-XXXX
        where XXXX increments sequentially across ALL students (AA01, AA02, ..., AA99, AB01, ...)
        """
        with transaction.atomic():
            # Get the last student number across ALL students
            last_student = Student.objects.filter(
                student_number__isnull=False
            ).exclude(
                student_number=''
            ).order_by('-student_number').first()
            
            if last_student and last_student.student_number:
                student_num = last_student.student_number
                try:
                    # Parse the student number (e.g., "AA01" -> prefix="AA", num=1)
                    # Extract letters and numbers
                    import re
                    match = re.match(r'^([A-Z]+)(\d+)$', student_num)
                    
                    if match:
                        prefix = match.group(1)
                        num_part = int(match.group(2))
                        
                        # Increment the number
                        if num_part < 99:
                            new_num = num_part + 1
                            next_student_num = f"{prefix}{str(new_num).zfill(2)}"
                        else:
                            # Need to increment the letter prefix
                            next_student_num = self._increment_prefix(prefix)
                    else:
                        next_student_num = "AA01"
                except (ValueError, IndexError):
                    next_student_num = "AA01"
            else:
                next_student_num = "AA01"
            
            # Store the student number for future reference
            self.student_number = next_student_num
            
            return f"{self.program.code}-{next_student_num}"
    
    def _increment_prefix(self, prefix):
        """
        Increment letter prefix: AA -> AB -> AC ... AZ -> BA -> BB ...
        """
        # Convert prefix to list of characters
        chars = list(prefix)
        
        # Start from the rightmost character
        i = len(chars) - 1
        
        while i >= 0:
            if chars[i] == 'Z':
                chars[i] = 'A'
                i -= 1
            else:
                chars[i] = chr(ord(chars[i]) + 1)
                break
        
        # If we've exhausted all characters, add a new 'A' at the beginning
        if i < 0:
            chars.insert(0, 'A')
        
        new_prefix = ''.join(chars)
        return f"{new_prefix}01"
    
    def get_absolute_url(self):
        return reverse('pass_book:student_list')
    
    def __str__(self):
        return f"{self.name} - {self.registration_number}"
    
    class Meta:
        ordering = ['student_number']
'''


from django.db import models, transaction
from django.conf import settings
from django.urls import reverse
import uuid
import re

'''
class Student(models.Model):
    SESSION_CHOICES = [
        ('D', 'Day'),
        ('E', 'Evening'),
        ('W', 'Weekend'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic student information
    student_photo = models.ImageField(
        upload_to='student_photos/',
        blank=True,
        null=True,
        help_text="Upload a clear face photo of the student"
    )
    parent_guardian_photo = models.ImageField(
        upload_to='parent_photos/',
        blank=True,
        null=True,
        help_text="Upload a clear face photo of the parent or guardian"
    )
    name = models.CharField(max_length=200)
    program = models.ForeignKey(
        'Program',
        on_delete=models.PROTECT,
        related_name='students'
    )
    nationality = models.CharField(max_length=100)
    student_contact = models.CharField(max_length=20)
    parent_guardian_name = models.CharField(max_length=200, blank=True, null=True)
    parent_guardian_contact = models.CharField(max_length=20, blank=True, null=True)
    parent_guardian_signature = models.ImageField(upload_to='parent_signatures/', blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Academic & Session Info
    admission_year = models.PositiveIntegerField(help_text="Year of admission (e.g., 2024)")
    session = models.CharField(max_length=1, choices=SESSION_CHOICES, help_text="Study session")
    expected_graduation_year = models.IntegerField(blank=True, null=True)
    
    # Manual Receipt
    manual_received = models.BooleanField(default=False)
    manual_received_date = models.DateField(blank=True, null=True)
    
    # Generated Fields (immutable after creation)
    registration_number = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Manual registration number (e.g., 909/24D/U/A001)"
    )
    program_code = models.CharField(max_length=10, blank=True, help_text="Copied from Program.code")
    student_number = models.CharField(max_length=10, blank=True, help_text="Sequential code like AA01")
    
    # NEW: Static access number field
    static_access_number = models.CharField(
        max_length=15, 
        unique=True, 
        blank=True, 
        help_text="Format: COURSE-XXXX (e.g., BAGC-AA01)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True,
        help_text="Linked user account for this student"
    )
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Generate static access number if not exists
        if not self.static_access_number:
            self.static_access_number = self.generate_static_access_number()
        
        # Copy program code if not set
        if not self.program_code and self.program:
            self.program_code = self.program.code
        
        super().save(*args, **kwargs)
        
        # Create user account after student is saved (only for new students)
        if is_new and not self.user:
            self.create_user_account()
    
    def create_user_account(self):
        """
        Create a user account for the student with:
        - Username: static_access_number
        - Password: 123
        - User type: student
        """
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        try:
            # Check if user already exists with this username
            if not User.objects.filter(username=self.static_access_number).exists():
                user = User.objects.create_user(
                    username=self.static_access_number,
                    password='123',  # Default password
                    user_type='student',
                    first_name=self.name.split()[0] if self.name else '',
                    last_name=' '.join(self.name.split()[1:]) if len(self.name.split()) > 1 else '',
                    email=f"{self.static_access_number}@student.example.com",  # Optional: set a placeholder email
                )
                
                # Link the user to this student
                self.user = user
                self.save(update_fields=['user'])
                
                print(f"✓ User account created for {self.name}: {self.static_access_number}")
        except Exception as e:
            print(f"✗ Error creating user account for {self.name}: {str(e)}")
    
    def generate_static_access_number(self):
        """
        Generate static access number in format: PROGRAM-XXXX
        where XXXX increments sequentially across ALL students (AA01, AA02, ..., AA99, AB01, ...)
        """
        with transaction.atomic():
            # Get the last student number across ALL students
            last_student = Student.objects.filter(
                student_number__isnull=False
            ).exclude(
                student_number=''
            ).order_by('-student_number').first()
            
            if last_student and last_student.student_number:
                student_num = last_student.student_number
                try:
                    # Parse the student number (e.g., "AA01" -> prefix="AA", num=1)
                    match = re.match(r'^([A-Z]+)(\d+)$', student_num)
                    
                    if match:
                        prefix = match.group(1)
                        num_part = int(match.group(2))
                        
                        # Increment the number
                        if num_part < 99:
                            new_num = num_part + 1
                            next_student_num = f"{prefix}{str(new_num).zfill(2)}"
                        else:
                            # Need to increment the letter prefix
                            next_student_num = self._increment_prefix(prefix)
                    else:
                        next_student_num = "AA01"
                except (ValueError, IndexError):
                    next_student_num = "AA01"
            else:
                next_student_num = "AA01"
            
            # Store the student number for future reference
            self.student_number = next_student_num
            
            return f"{self.program.code}-{next_student_num}"
    
    def _increment_prefix(self, prefix):
        """
        Increment letter prefix: AA -> AB -> AC ... AZ -> BA -> BB ...
        """
        chars = list(prefix)
        i = len(chars) - 1
        
        while i >= 0:
            if chars[i] == 'Z':
                chars[i] = 'A'
                i -= 1
            else:
                chars[i] = chr(ord(chars[i]) + 1)
                break
        
        if i < 0:
            chars.insert(0, 'A')
        
        new_prefix = ''.join(chars)
        return f"{new_prefix}01"
    
    def get_absolute_url(self):
        return reverse('pass_book:student_list')
    
    def __str__(self):
        return f"{self.name} - {self.registration_number}"
    
    class Meta:
        ordering = ['student_number']
'''
from django.db import models, transaction
from django.conf import settings
from django.urls import reverse
import uuid
import re


from django.db import models, transaction
from django.conf import settings
from django.urls import reverse
import uuid
import re

from django.db import models, transaction
from django.conf import settings
from django.urls import reverse
import uuid
import re


class Student(models.Model):
    SESSION_CHOICES = [
        ('D', 'Day'),
        ('E', 'Evening'),
        ('W', 'Weekend'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic student information
    student_photo = models.ImageField(
        upload_to='student_photos/',
        blank=True,
        null=True,
        help_text="Upload a clear face photo of the student"
    )
    parent_guardian_photo = models.ImageField(
        upload_to='parent_photos/',
        blank=True,
        null=True,
        help_text="Upload a clear face photo of the parent or guardian"
    )
    name = models.CharField(max_length=200)
    program = models.ForeignKey(
        'Program',
        on_delete=models.PROTECT,
        related_name='students'
    )
    nationality = models.CharField(max_length=100)
    student_contact = models.CharField(max_length=20)
    parent_guardian_name = models.CharField(max_length=200, blank=True, null=True)
    parent_guardian_contact = models.CharField(max_length=20, blank=True, null=True)
    parent_guardian_signature = models.ImageField(upload_to='parent_signatures/', blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Academic & Session Info
    admission_year = models.PositiveIntegerField(help_text="Year of admission (e.g., 2024)")
    session = models.CharField(max_length=1, choices=SESSION_CHOICES, help_text="Study session")
    expected_graduation_year = models.IntegerField(blank=True, null=True)
    
    # Manual Receipt
    manual_received = models.BooleanField(default=False)
    manual_received_date = models.DateField(blank=True, null=True)
    
    # Generated Fields (immutable after creation)
    registration_number = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Manual registration number (e.g., 909/24D/U/A001)"
    )
    program_code = models.CharField(max_length=10, blank=True, help_text="Copied from Program.code")
    student_number = models.CharField(max_length=10, blank=True, help_text="Sequential code like AA01")
    
    # NEW: Static access number field
    static_access_number = models.CharField(
        max_length=15, 
        unique=True, 
        blank=True, 
        help_text="Format: COURSE-XXXX (e.g., BAGC-AA01)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True,
        help_text="Linked user account for this student"
    )
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Generate static access number if not exists
        if not self.static_access_number:
            self.static_access_number = self.generate_static_access_number()
        
        # Copy program code if not set
        if not self.program_code and self.program:
            self.program_code = self.program.code
        
        super().save(*args, **kwargs)
        
        # Create user account after student is saved (only for new students)
        if is_new and not self.user:
            self.create_user_account()
    
    def create_user_account(self):
        """
        Create a user account for the student with:
        - Username: static_access_number
        - Password: 123
        - User type: student
        """
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        try:
            # Check if user already exists with this username
            if not User.objects.filter(username=self.static_access_number).exists():
                user = User.objects.create_user(
                    username=self.static_access_number,
                    password='123',  # Default password
                    user_type='student',
                    first_name=self.name.split()[0] if self.name else '',
                    last_name=' '.join(self.name.split()[1:]) if len(self.name.split()) > 1 else '',
                    email=f"{self.static_access_number}@student.example.com",  # Optional: set a placeholder email
                )
                
                # Link the user to this student
                self.user = user
                self.save(update_fields=['user'])
                
                print(f"✓ User account created for {self.name}: {self.static_access_number}")
        except Exception as e:
            print(f"✗ Error creating user account for {self.name}: {str(e)}")
    
    def generate_static_access_number(self):
        """
        Generate static access number in format: COURSE-XXXX
        where COURSE is the Course code (abbreviation like BAGC, BAIT, BAM)
        and XXXX increments sequentially across ALL students (AA01, AA02, ..., AA99, AB01, ...)
        """
        with transaction.atomic():
            # Get the Course code for this student's program
            # Try to get the first active course for the program, or first course if none active
            course_code = None
            if self.program:
                # Use Course model - will be available at runtime when method is called
                course = Course.objects.filter(program=self.program, is_active=True).first()
                if not course:
                    course = Course.objects.filter(program=self.program).first()
                if course:
                    course_code = course.code
            
            # Fall back to program code if no course found
            if not course_code:
                course_code = self.program.code if self.program else "UNKNOWN"
            
            # Get the last student number across ALL students
            last_student = Student.objects.filter(
                student_number__isnull=False
            ).exclude(
                student_number=''
            ).order_by('-student_number').first()
            
            if last_student and last_student.student_number:
                student_num = last_student.student_number
                try:
                    # Parse the student number (e.g., "AA01" -> prefix="AA", num=1)
                    match = re.match(r'^([A-Z]+)([0-9]+)$', student_num)
                    
                    if match:
                        prefix = match.group(1)
                        num_part = int(match.group(2))
                        
                        # Increment the number
                        if num_part < 99:
                            new_num = num_part + 1
                            next_student_num = f"{prefix}{str(new_num).zfill(2)}"
                        else:
                            # Need to increment the letter prefix
                            next_student_num = self._increment_prefix(prefix)
                    else:
                        next_student_num = "AA01"
                except (ValueError, IndexError):
                    next_student_num = "AA01"
            else:
                next_student_num = "AA01"
            
            # Store the student number for future reference
            self.student_number = next_student_num
            
            return f"{course_code}-{next_student_num}"
    
    def _increment_prefix(self, prefix):
        """
        Increment letter prefix: AA -> AB -> AC ... AZ -> BA -> BB ...
        """
        chars = list(prefix)
        i = len(chars) - 1
        
        while i >= 0:
            if chars[i] == 'Z':
                chars[i] = 'A'
                i -= 1
            else:
                chars[i] = chr(ord(chars[i]) + 1)
                break
        
        if i < 0:
            chars.insert(0, 'A')
        
        new_prefix = ''.join(chars)
        return f"{new_prefix}01"
    
    def get_absolute_url(self):
        return reverse('pass_book:student_list')
    
    def __str__(self):
        return f"{self.name} - {self.registration_number}"
    
    class Meta:
        ordering = ['student_number']

class AcademicYear(models.Model):
    """Academic year definition"""
    year_label = models.CharField(max_length=20, unique=True, help_text="e.g., 2023-2024")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.year_label


class Semester(models.Model):
    """Semester information"""
    SEMESTER_CHOICES = [
        (1, 'Semester One'),
        (2, 'Semester Two'),
        (3, 'Semester Three'),
        (4, 'Semester Four'),
        (5, 'Semester Five'),
        (6, 'Semester Six'),
        (7, 'Semester Seven'),
        (8, 'Semester Eight'),
    ]
    number = models.IntegerField(choices=SEMESTER_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(8)])
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ['number', 'academic_year']  # Prevent duplicate semester numbers in same year
        ordering = ['academic_year', 'number']

    def __str__(self):
        return f"Semester {self.number} ({self.academic_year.year_label})"
    
    @property
    def semester_code(self):
        """Return semester code in format S1, S2, etc."""
        return f"S{self.number}"



class AccessNumber(models.Model):
    """
    Semester-specific access number that references the static student information.
    Format: PROGRAM-SEMESTER-XXX (e.g., 909-S1-A001)
    """
    # This will be the full access number with semester code
    access_number = models.CharField(max_length=20, unique=True, primary_key=True)
    
    # Reference to the static student information
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='access_numbers'
    )
    
    # Semester-specific information
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE)
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)
    year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Generation tracking
    generated_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['student', 'academic_year', 'semester']
        ordering = ['-generated_date']
    
    def save(self, *args, **kwargs):
        # Ensure student has static access number before generating semester-specific one
        if not self.student.static_access_number:
            self.student.save()  # This will trigger static access number generation
        
        if not self.access_number:
            self.access_number = self.generate_access_number()
        super().save(*args, **kwargs)
    
    def generate_access_number(self):
        """
        Generate access number by inserting semester code into static access number
        Static format: COURSE-STUDENT (e.g., BAGC-AA01)
        Semester format: COURSE-SEMESTER-STUDENT (e.g., BAGC-S1-AA01)
        
        Format: COURSE-SEMESTER-STUDENT
        e.g., BAGC-S1-AA01 (from static BAGC-AA01)
        """
        # Split the static access number: "BAGC-AA01" -> ["BAGC", "AA01"]
        static_parts = self.student.static_access_number.split('-')
        
        # Insert semester code between course code and student number
        return (
            f"{static_parts[0]}-"           # Course code (BAGC, BAIT, etc.)
            f"{self.semester.semester_code}-"  # Semester (S1, S2, etc.)
            f"{static_parts[1]}"            # Student sequence (AA01)
        )
    
    def __str__(self):
        return f"{self.access_number} - {self.student.name}"


class AccessNumberUtils:
    """
    Utility class for access number operations
    """
    
    @staticmethod
    def create_semester_access_number(student, academic_year, semester, year_of_study):
        """
        Create a new semester-specific access number for a student
        """
        # Ensure static access number exists
        if not student.static_access_number:
            student.save()
        
        # Generate access number before saving
        access_num = AccessNumber(
            student=student,
            academic_year=academic_year,
            semester=semester,
            year_of_study=year_of_study
        )
        access_num.access_number = access_num.generate_access_number()
        access_num.save()
        return access_num
    
    @staticmethod
    def get_student_current_access_number(student, academic_year, semester):
        """
        Get the current access number for a student in a specific semester
        """
        try:
            return AccessNumber.objects.get(
                student=student,
                academic_year=academic_year,
                semester=semester,
                is_active=True
            )
        except AccessNumber.DoesNotExist:
            return None
    
    @staticmethod
    def bulk_generate_access_numbers(students, academic_year, semester, year_of_study):
        """
        Bulk generate access numbers for multiple students
        """
        access_numbers = []
        for student in students:
            # Skip if already exists
            if AccessNumber.objects.filter(
                student=student,
                academic_year=academic_year,
                semester=semester
            ).exists():
                continue

            # Ensure student has static_access_number
            if not student.static_access_number:
                student.save()

            # Create instance and generate PK before bulk_create
            access_num = AccessNumber(
                student=student,
                academic_year=academic_year,
                semester=semester,
                year_of_study=year_of_study
            )
            access_num.access_number = access_num.generate_access_number()
            access_numbers.append(access_num)

        # Bulk insert with pre-generated PKs
        created_access_numbers = AccessNumber.objects.bulk_create(access_numbers)
        return created_access_numbers


class Course(models.Model):
    """Top-level course structure (e.g., Bachelor's program courses)"""
    LEVEL_CHOICES = [
        ('UNDERGRAD', 'Undergraduate'),
        ('POSTGRAD', 'Postgraduate'),
    ]
    
    code = models.CharField(max_length=10, unique=True, help_text="Course code (e.g., BSCS)")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='UNDERGRAD')
    duration = models.IntegerField(help_text="Duration in years")
    program = models.ForeignKey(
        Program, 
        on_delete=models.CASCADE, 
        related_name='courses'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class CourseUnit(models.Model):
    """Course units/modules offered within a course"""
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    credit_units = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    description = models.TextField(blank=True, null=True)
    department = models.CharField(max_length=100)
    semester_offered = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    is_active = models.BooleanField(default=True)
    
    # Hierarchical relationships
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='course_units'
    )
    
    class Meta:
        verbose_name = "Course Unit"
        verbose_name_plural = "Course Units"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.title}"


class CourseWork(models.Model):
    """Course works/assignments within course units"""
    title = models.CharField(max_length=200)
    course_unit = models.ForeignKey(
        CourseUnit, 
        on_delete=models.CASCADE, 
        related_name='course_works'
    )
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    max_score = models.IntegerField(default=100)
    
    class Meta:
        verbose_name = "Course Work"
        verbose_name_plural = "Course Works"
        ordering = ['title']
    
    def __str__(self):
        return f"{self.course_unit.code} - {self.title}"


class SemesterRegistration(models.Model):
    """
    Student registration for each semester - now linked via AccessNumber.
    All other models reference this through access_number for complete traceability.
    """
    access_number = models.OneToOneField(
        AccessNumber, 
        on_delete=models.CASCADE, 
        primary_key=True, 
        related_name='semester_registration'
    )
    
    # Finance Department Clearance
    finance_cleared = models.BooleanField(default=False)
    finance_officer_name = models.CharField(max_length=200, blank=True, null=True)
    finance_officer_designation = models.CharField(max_length=200, blank=True, null=True)
    finance_clearance_date = models.DateField(blank=True, null=True)
    finance_signature = models.ImageField(upload_to='finance_signatures/', blank=True, null=True)
    
    # Academic Registrar's Department
    academic_cleared = models.BooleanField(default=False)
    academic_officer_name = models.CharField(max_length=200, blank=True, null=True)
    academic_officer_designation = models.CharField(max_length=200, blank=True, null=True)
    academic_clearance_date = models.DateField(blank=True, null=True)
    academic_signature = models.ImageField(upload_to='academic_signatures/', blank=True, null=True)
    
    # Dean of Students Department - Orientation
    orientation_cleared = models.BooleanField(default=False)
    dos_orientation_officer_name = models.CharField(max_length=200, blank=True, null=True)
    dos_orientation_designation = models.CharField(max_length=200, blank=True, null=True)
    orientation_date = models.DateField(blank=True, null=True)
    dos_orientation_signature = models.ImageField(upload_to='dos_orientation_signatures/', blank=True, null=True)
    
    # Items received during orientation
    undergraduate_gown_received = models.BooleanField(default=False)
    tshirt_received = models.BooleanField(default=False)
    association_membership_card_received = models.BooleanField(default=False)
    
    # Dean of Students Department - Assimilation
    assimilation_cleared = models.BooleanField(default=False)
    dos_assimilation_officer_name = models.CharField(max_length=200, blank=True, null=True)
    dos_assimilation_designation = models.CharField(max_length=200, blank=True, null=True)
    assimilation_date = models.DateField(blank=True, null=True)
    dos_assimilation_signature = models.ImageField(upload_to='dos_assimilation_signatures/', blank=True, null=True)
    
    # Items received during assimilation
    admission_letter_received = models.BooleanField(default=False)
    student_id_received = models.BooleanField(default=False)  # For new students
    examination_card_received = models.BooleanField(default=False)  # For continuing students
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def student(self):
        """Convenience property to access student via access_number"""
        return self.access_number.student
    
    @property
    def semester(self):
        """Convenience property to access semester via access_number"""
        return self.access_number.semester
    
    @property
    def academic_year(self):
        """Convenience property to access academic year via access_number"""
        return self.access_number.academic_year
    
    def __str__(self):
        return f"{self.access_number.access_number} - {self.student.name}"


class StudentCourseUnit(models.Model):
    """Student's course unit registration and status - linked via access_number"""
    STATUS_CHOICES = [
        ('PASSED', 'Passed'),
        ('MISSED', 'Missed'),
        ('RETAKE', 'Retake'),
    ]
    
    access_number = models.ForeignKey(
        AccessNumber, 
        on_delete=models.CASCADE, 
        related_name='course_units'
    )
    course_unit = models.ForeignKey(CourseUnit, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, null=True)
    
    # HOD Certification
    hod_certified = models.BooleanField(default=False)
    hod_name = models.CharField(max_length=200, blank=True, null=True)
    hod_designation = models.CharField(max_length=200, blank=True, null=True)
    hod_department = models.CharField(max_length=100, blank=True, null=True)
    hod_certification_date = models.DateField(blank=True, null=True)
    hod_signature = models.ImageField(upload_to='hod_signatures/', blank=True, null=True)
    
    class Meta:
        unique_together = ['access_number', 'course_unit']
        verbose_name = "Student Course Unit"
        verbose_name_plural = "Student Course Units"
    
    def __str__(self):
        return f"{self.access_number.access_number} - {self.course_unit.code} - {self.status or 'Pending'}"


class StudentCourseWork(models.Model):
    """Student's course work completion status - linked via access_number"""
    STATUS_CHOICES = [
        ('DONE', 'Done'),
        ('MISSED', 'Missed'),
    ]
    
    access_number = models.ForeignKey(
        AccessNumber, 
        on_delete=models.CASCADE, 
        related_name='course_works'
    )
    course_work = models.ForeignKey(CourseWork, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)
    
    # HOD Certification
    hod_certified = models.BooleanField(default=False)
    hod_name = models.CharField(max_length=200, blank=True, null=True)
    hod_designation = models.CharField(max_length=200, blank=True, null=True)
    hod_department = models.CharField(max_length=100, blank=True, null=True)
    hod_certification_date = models.DateField(blank=True, null=True)
    hod_signature = models.ImageField(upload_to='hod_coursework_signatures/', blank=True, null=True)
    
    class Meta:
        unique_together = ['access_number', 'course_work']
        verbose_name = "Student Course Work"
        verbose_name_plural = "Student Course Works"
    
    def __str__(self):
        return f"{self.access_number.access_number} - {self.course_work.title} - {self.status or 'Pending'}"


class Association(models.Model):
    """Student associations and clubs"""
    ASSOCIATION_TYPES = [
        ('GUILD', 'Guild Association'),
        ('CLUB', 'Club'),
    ]
    
    name = models.CharField(max_length=200)
    association_type = models.CharField(max_length=10, choices=ASSOCIATION_TYPES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_association_type_display()})"


class StudentAssociation(models.Model):
    """Student's association/club membership - linked via access_number"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]
    
    access_number = models.ForeignKey(
        AccessNumber, 
        on_delete=models.CASCADE, 
        related_name='associations'
    )
    association = models.ForeignKey(Association, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    join_date = models.DateField(auto_now_add=True)
    
    # Dean of Students Certification
    dos_certified = models.BooleanField(default=False)
    dos_name = models.CharField(max_length=200, blank=True, null=True)
    dos_designation = models.CharField(max_length=200, blank=True, null=True)
    dos_department = models.CharField(max_length=100, blank=True, null=True)
    dos_certification_date = models.DateField(blank=True, null=True)
    dos_signature = models.ImageField(upload_to='dos_association_signatures/', blank=True, null=True)
    
    class Meta:
        unique_together = ['access_number', 'association']
    
    def __str__(self):
        return f"{self.access_number.access_number} - {self.association.name} - {self.status}"

   

class DeadSemesterApplication(models.Model):
    """Application for dead semester/year"""
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='dead_semester_applications'
    )
    application_type = models.CharField(max_length=20, choices=[('SEMESTER', 'Dead Semester'), ('YEAR', 'Dead Year')])
    dead_semester = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(2)])
    dead_year = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    reason = models.TextField()
    application_date = models.DateField(auto_now_add=True)
    
    # Recommendations
    hod_recommended = models.BooleanField(default=False)
    hod_name = models.CharField(max_length=200, blank=True, null=True)
    hod_designation = models.CharField(max_length=200, blank=True, null=True)
    hod_department = models.CharField(max_length=100, blank=True, null=True)
    hod_signature = models.ImageField(upload_to='hod_dead_semester_signatures/', blank=True, null=True)
    hod_date = models.DateField(blank=True, null=True)
    
    faculty_recommended = models.BooleanField(default=False)
    faculty_name = models.CharField(max_length=200, blank=True, null=True)
    faculty_designation = models.CharField(max_length=200, blank=True, null=True)
    faculty_department = models.CharField(max_length=100, blank=True, null=True)
    faculty_signature = models.ImageField(upload_to='faculty_dead_semester_signatures/', blank=True, null=True)
    faculty_date = models.DateField(blank=True, null=True)
    
    registrar_recommended = models.BooleanField(default=False)
    registrar_name = models.CharField(max_length=200, blank=True, null=True)
    registrar_designation = models.CharField(max_length=200, blank=True, null=True)
    registrar_department = models.CharField(max_length=100, blank=True, null=True)
    registrar_signature = models.ImageField(upload_to='registrar_dead_semester_signatures/', blank=True, null=True)
    registrar_date = models.DateField(blank=True, null=True)
    
    # Final approval
    @property
    def approved(self):
        return (
            self.hod_recommended and
            self.faculty_recommended and
            self.registrar_recommended
        )


    @property
    def approval_status(self):
        count = sum([
            self.hod_recommended,
            self.faculty_recommended,
            self.registrar_recommended
        ])
        if count == 3:
            return "APPROVED"
        elif count > 0:
            return "PARTIALLY_APPROVED"
        else:
            return "PENDING"

    @property
    def verified(self):
        """Alias for approved — or you can add extra logic here"""
        return self.approved

    # Optional: For Django Admin or serializers, expose as method
    def is_approved(self):
        return self.approved
    is_approved.boolean = True  # Shows as green/red icon in Django admin
    is_approved.short_description = "Approved"
    
    def __str__(self):
        return f"{self.student.name} - Dead {self.application_type} Application"


class ResumptionApplication(models.Model):
    """Application to resume studies"""
    dead_semester_application = models.OneToOneField(
        DeadSemesterApplication, 
        on_delete=models.CASCADE, 
        related_name='resumption'
    )
    resume_semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    resume_academic_year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    reason = models.TextField()
    application_date = models.DateField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.dead_semester_application.student.name} - Resumption Application"



from decimal import Decimal

class BbalaLaptopScheme(models.Model):
    student = models.OneToOneField(
        Student, 
        on_delete=models.CASCADE, 
        related_name='laptop_scheme'
    )
    total_cost = models.DecimalField(max_digits=10, decimal_places=0, default=Decimal('1500000'))  # ✅ Decimal
    laptop_serial_number = models.CharField(max_length=100, blank=True, null=True)
    payment_made = models.DecimalField(max_digits=10, decimal_places=0, default=Decimal('0'))     # ✅ Decimal
    balance = models.DecimalField(max_digits=10, decimal_places=0, default=Decimal('1500000'))    # ✅ Decimal
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # ✅ Safe: both are Decimal
        self.balance = self.total_cost - self.payment_made
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.name} - Laptop Scheme (Balance: UGX {self.balance})"

class MedicalRegistration(models.Model):
    """Student medical registration - linked via access_number"""
    access_number = models.OneToOneField(
        AccessNumber, 
        on_delete=models.CASCADE, 
        related_name='medical_registration'
    )
    medical_officer_name = models.CharField(max_length=200)
    registration_date = models.DateField(auto_now_add=True)
    medical_officer_signature = models.ImageField(upload_to='medical_signatures/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.access_number.access_number} - Medical Registration"


class NCHERegistration(models.Model):
    """NCHE payment registration - linked via access_number"""
    access_number = models.OneToOneField(
        AccessNumber, 
        on_delete=models.CASCADE, 
        related_name='nche_registration'
    )
    officer_name = models.CharField(max_length=200)
    registration_date = models.DateField(auto_now_add=True)
    officer_signature = models.ImageField(upload_to='nche_signatures/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.access_number.access_number} - NCHE Registration"


class Internship(models.Model):
    """Student internship record - linked via access_number"""
    STATUS_CHOICES = [
        ('DONE', 'Done'),
        ('NOT_DONE', 'Not Done'),
    ]
    
    access_number = models.OneToOneField(
        AccessNumber, 
        on_delete=models.CASCADE, 
        related_name='internship'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NOT_DONE')
    company_name = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    supervisor_name = models.CharField(max_length=200, blank=True, null=True)
    supervisor_contact = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"{self.access_number.access_number} - Internship ({self.status})"


class SemesterClearance(models.Model):
    """End of semester clearance - linked via access_number"""
    access_number = models.OneToOneField(
        AccessNumber, 
        on_delete=models.CASCADE, 
        related_name='clearance'
    )
    
    # Finance Clearance
    finance_cleared = models.BooleanField(default=False)
    finance_officer_name = models.CharField(max_length=200, blank=True, null=True)
    finance_officer_designation = models.CharField(max_length=200, blank=True, null=True)
    finance_clearance_date = models.DateField(blank=True, null=True)
    finance_signature = models.ImageField(upload_to='finance_clearance_signatures/', blank=True, null=True)
    
    # Academic Clearance
    academic_cleared = models.BooleanField(default=False)
    academic_officer_name = models.CharField(max_length=200, blank=True, null=True)
    academic_officer_designation = models.CharField(max_length=200, blank=True, null=True)
    academic_clearance_date = models.DateField(blank=True, null=True)
    academic_signature = models.ImageField(upload_to='academic_clearance_signatures/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.access_number.access_number} - Semester Clearance"

from django.db import models

class GraduationClearance(models.Model):
    """Final graduation clearance"""
    student = models.OneToOneField(
        Student, 
        on_delete=models.CASCADE, 
        related_name='graduation_clearance'
    )
    all_requirements_met = models.BooleanField(default=False)
    clearance_date = models.DateField(blank=True, null=True)
    
    # Final approving officer
    approving_officer_name = models.CharField(max_length=200, blank=True, null=True)
    approving_officer_designation = models.CharField(max_length=200, blank=True, null=True)
    approving_officer_signature = models.ImageField(
        upload_to='graduation_signatures/', 
        blank=True, 
        null=True
        # Removed any file size or content type restrictions
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.name} - Graduation Clearance"

