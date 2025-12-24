# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('sysadmin', 'System Administrator'),
        ('student', 'Student'),
        ('dean_of_students', 'Dean of Students'),
        ('finance_director', 'Finance Director'),
        ('academic_registrar', 'Academic Registrar'),
        ('head_of_department', 'Head of Department'),
        ('faculty_dean', 'Faculty Dean'),
        ('medical_officer', 'Medical Officer'),
        ('nche_officer', 'NCHE Officer'),
        ('lecturer', 'Lecturer'),  # Keep if needed
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    # Backward compatibility
    @property
    def is_sysadmin(self):
        return self.user_type == 'sysadmin'

    @property
    def is_student(self):
        return self.user_type == 'student'

    @property
    def is_dean_of_students(self):
        return self.user_type == 'dean_of_students'

    @property
    def is_finance_director(self):
        return self.user_type == 'finance_director'

    @property
    def is_academic_registrar(self):
        return self.user_type == 'academic_registrar'

    @property
    def is_head_of_department(self):
        return self.user_type == 'head_of_department'

    @property
    def is_faculty_dean(self):
        return self.user_type == 'faculty_dean'

    @property
    def is_medical_officer(self):
        return self.user_type == 'medical_officer'

    @property
    def is_nche_officer(self):
        return self.user_type == 'nche_officer'

    # Fix reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name="accounts_user_groups",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="accounts_user_permissions",
        blank=True,
    )

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"