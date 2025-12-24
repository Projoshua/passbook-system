
# forms.py - ADD THIS AT THE TOP
from django.apps import apps

def get_model(model_name):
    """Safely get model using lazy loading to prevent circular imports"""
    return apps.get_model('pass_book', model_name)
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import StudentAssociation, Association, AccessNumber
from django.forms import modelformset_factory
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import StudentAssociation, Association, AccessNumber


from django import forms
from django.forms import inlineformset_factory
from .models import (
    Student, AcademicYear, Semester, AccessNumber, SemesterRegistration,
    CourseUnit, StudentCourseUnit, CourseWork, StudentCourseWork,
    Association, StudentAssociation, DeadSemesterApplication,
    ResumptionApplication, BbalaLaptopScheme, MedicalRegistration,
    NCHERegistration, Internship, SemesterClearance, GraduationClearance
)
from django.core.exceptions import ValidationError
from datetime import datetime
from django.forms import inlineformset_factory
# forms.py
from django.db.models import Q, F, Value, When, Case
from .models import CourseWork, StudentCourseWork, AccessNumber
from django import forms
from .models import Student, Program
from django.utils import timezone

# In forms.py, add these imports
from django import forms
from .models import Student, AcademicYear, Semester

# forms.py
from django import forms
from .models import Student, Program
from .models import Program, Course, CourseUnit, CourseWork
# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import transaction
from .models import Student




# Form for Program model
class ProgramForm(forms.ModelForm):
    class Meta:
        model = get_model('Program')
        fields = ['code', 'name', 'description', 'faculty', 'duration', 'is_active']

# Form for Course model
class CourseForm(forms.ModelForm):
    class Meta:
        model = get_model('Course')
        fields = ['code', 'name', 'description', 'level', 'duration', 'program', 'is_active']


from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Student, Program

from django import forms
from django.core.exceptions import ValidationError
from .models import Student

class StudentForm(forms.ModelForm):
    """Form for creating/editing students with manual registration number"""
    
    class Meta:
        model = Student
        fields = [
            'registration_number',
            'name',
            'student_photo',
            'parent_guardian_photo',
            'program',
            'nationality',
            'student_contact',
            'parent_guardian_name',
            'parent_guardian_contact',
            'parent_guardian_signature',
            'signature',
            'serial_number',
            'admission_year',
            'session',
            'expected_graduation_year',
            'manual_received',
            'manual_received_date',
        ]
        widgets = {
            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 909/24D/U/A001',
                'autocomplete': 'off',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name of the student'
            }),
            'program': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'student_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+256 xxx xxx xxx'
            }),
            'parent_guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_guardian_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'admission_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2000',
                'max': '2100'
            }),
            'session': forms.Select(attrs={'class': 'form-control'}),
            'expected_graduation_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2000',
                'max': '2100'
            }),
            'manual_received': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'manual_received_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_registration_number(self):
        """Validate registration number"""
        registration_number = self.cleaned_data.get('registration_number')
        
        if not registration_number:
            raise ValidationError("Registration number is required")
        
        # Basic validation
        if len(registration_number.strip()) < 5:
            raise ValidationError("Registration number is too short")
        
        # Check for duplicates (only for new students)
        if self.instance and self.instance.pk:
            # For editing - check if changed
            if registration_number != self.instance.registration_number:
                if Student.objects.filter(registration_number=registration_number).exists():
                    raise ValidationError(
                        f"Registration number '{registration_number}' already exists."
                    )
        else:
            # For new student
            if Student.objects.filter(registration_number=registration_number).exists():
                raise ValidationError(
                    f"Registration number '{registration_number}' already exists."
                )
        
        return registration_number
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        
        # Validate admission year
        admission_year = cleaned_data.get('admission_year')
        if admission_year:
            from datetime import datetime
            current_year = datetime.now().year
            if admission_year < 2000 or admission_year > current_year + 1:
                self.add_error('admission_year', 
                             f"Admission year must be between 2000 and {current_year + 1}")
        
        # Validate expected graduation year
        expected_graduation_year = cleaned_data.get('expected_graduation_year')
        if expected_graduation_year and admission_year:
            if expected_graduation_year <= admission_year:
                self.add_error('expected_graduation_year',
                             "Graduation year must be after admission year")
        
        return cleaned_data



class AcademicYearForm(forms.ModelForm):
    """Form for academic year management with enhanced validation"""
    
    class Meta:
        model = get_model('AcademicYear')
        fields = ['year_label', 'start_date', 'end_date', 'is_active']
        widgets = {
            'year_label': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '2024-2025',
                'pattern': r'\d{4}-\d{4}',
                'title': 'Format: YYYY-YYYY (e.g., 2024-2025)'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_year_label(self):
        """Validate year label format"""
        year_label = self.cleaned_data.get('year_label')
        
        if year_label:
            # Check format: YYYY-YYYY
            import re
            if not re.match(r'^\d{4}-\d{4}$', year_label):
                raise ValidationError("Year label must be in format: YYYY-YYYY (e.g., 2024-2025)")
            
            # Check if years are consecutive
            start_year, end_year = map(int, year_label.split('-'))
            if end_year != start_year + 1:
                raise ValidationError("End year must be exactly one year after start year")
                
        return year_label

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date.")
            
            # Validate that the date range matches the year label
            year_label = cleaned_data.get('year_label')
            if year_label:
                start_year = start_date.year
                end_year = end_date.year
                expected_years = year_label.split('-')
                
                if str(start_year) != expected_years[0] or str(end_year) != expected_years[1]:
                    raise ValidationError(
                        "Date range must match the year label. "
                        f"Start date should be in {expected_years[0]}, "
                        f"end date in {expected_years[1]}."
                    )
        
        return cleaned_data



class GenerateAccessNumberForm(forms.Form):
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label="Academic Year",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        label="Semester",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year_of_study = forms.IntegerField(
        min_value=1,
        max_value=5,
        initial=1,
        label="Year of Study",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class BulkGenerateAccessNumberForm(forms.Form):
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.filter(static_access_number__isnull=False),
        label="Select Students",
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 10})
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label="Academic Year",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        label="Semester",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year_of_study = forms.IntegerField(
        min_value=1,
        max_value=5,
        initial=1,
        label="Year of Study",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        search_query = kwargs.pop('search_query', '')
        super().__init__(*args, **kwargs)
        
        queryset = Student.objects.filter(static_access_number__isnull=False)
        
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(registration_number__icontains=search_query) |
                Q(static_access_number__icontains=search_query) |
                Q(student_number__icontains=search_query) |
                Q(program_code__icontains=search_query)
            )
        
        self.fields['students'].queryset = queryset


'''
# forms.py
class AccessNumberForm(forms.ModelForm):
    class Meta:
        model = get_model('AccessNumber')
        fields = ['student', 'academic_year', 'semester', 'year_of_study']
        # Remove access_number field since it's auto-generated
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show students with complete static information
        self.fields['student'].queryset = Student.objects.exclude(
            Q(university_code__isnull=True) | 
            Q(admission_year__isnull=True) |
            Q(program_code__isnull=True) |
            Q(student_number__isnull=True)
        )



# forms.py
class AccessNumberUpdateForm(forms.ModelForm):
    class Meta:
        model = get_model('AccessNumber')
        fields = ['is_active', 'academic_year', 'semester', 'year_of_study']
        # Exclude access_number since it shouldn't be changed
'''


class SemesterForm(forms.ModelForm):
    class Meta:
        model = get_model('Semester')
        fields = ['number', 'academic_year', 'start_date', 'end_date', 'is_active']
        widgets = {
            'number': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        def clean(self):
            cleaned_data = super().clean()
            start_date = cleaned_data.get("start_date")
            end_date = cleaned_data.get("end_date")

            if start_date and end_date and start_date > end_date:
                raise forms.ValidationError("Start date must be before end date.")
                return cleaned_data
        help_texts = {
            'is_active': 'Check this to make the semester active. Other active semesters will be deactivated automatically.',
        }




class SemesterRegistrationForm(forms.ModelForm):
    """Form for semester registration clearances"""
    
    class Meta:
        model = get_model('SemesterRegistration')
        fields = [
            # Finance Department
            'finance_cleared', 'finance_officer_name', 'finance_officer_designation',
            'finance_clearance_date', 'finance_signature',
            # Academic Registrar
            'academic_cleared', 'academic_officer_name', 'academic_officer_designation',
            'academic_clearance_date', 'academic_signature',
            # Orientation
            'orientation_cleared', 'dos_orientation_officer_name', 'dos_orientation_designation',
            'orientation_date', 'dos_orientation_signature',
            'undergraduate_gown_received', 'tshirt_received', 'association_membership_card_received',
            # Assimilation
            'assimilation_cleared', 'dos_assimilation_officer_name', 'dos_assimilation_designation',
            'assimilation_date', 'dos_assimilation_signature',
            'admission_letter_received', 'student_id_received', 'examination_card_received'
        ]
        widgets = {
            'finance_officer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'finance_officer_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'finance_clearance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'academic_officer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_officer_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_clearance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dos_orientation_officer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dos_orientation_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'orientation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dos_assimilation_officer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dos_assimilation_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'assimilation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class CourseUnitForm(forms.ModelForm):
    """Form for course unit management"""
    
    class Meta:
        model = CourseUnit
        fields = ['code', 'title', 'credit_units', 'department', 'semester_offered', 'is_active', 'course']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CSC101'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'credit_units': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'semester_offered': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 8}),
        }

    def clean_code(self):
        code = self.cleaned_data['code'].upper()
        return code


# forms.py


class StudentCourseUnitForm(forms.ModelForm):
    class Meta:
        model = get_model('StudentCourseUnit')
        fields = [
            'course_unit', 'status',
            'hod_certified', 'hod_name', 'hod_designation',
            'hod_department', 'hod_certification_date', 'hod_signature'
        ]
        widgets = {
            'hod_certification_date': forms.DateInput(attrs={'type': 'date'}),
            'hod_name': forms.TextInput(attrs={'placeholder': 'e.g., Dr. Jane Muthoni'}),
            'hod_designation': forms.TextInput(attrs={'placeholder': 'Head of Department'}),
            'hod_department': forms.TextInput(attrs={'placeholder': 'e.g., Computer Science'}),
        }

    def __init__(self, *args, access_num=None, **kwargs):
        super().__init__(*args, **kwargs)
        if access_num:
            # Exclude already registered course units
            existing = StudentCourseUnit.objects.filter(access_number=access_num)
            self.fields['course_unit'].queryset = CourseUnit.objects.exclude(
                pk__in=existing.values_list('course_unit__pk', flat=True)
            )
        # Make course_unit required
        self.fields['course_unit'].required = True


# Formset
StudentCourseUnitFormSet = forms.inlineformset_factory(
    AccessNumber,
    StudentCourseUnit,
    form=StudentCourseUnitForm,
    extra=5,  # Allow up to 5 new entries
    can_delete=True,
)


class CourseWorkForm(forms.ModelForm):
    """Form for course work management"""
    
    class Meta:
        model = get_model('CourseWork')
        fields = ['title', 'course_unit', 'description', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'course_unit': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }



class AssignCourseWorkForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=AccessNumber.objects.none(),
        required=True,
        label="Student"
    )

    class Meta:
        model = get_model('StudentCourseWork')
        fields = ['student', 'status', 'submission_date']
        widgets = {
            'submission_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        course_work = kwargs.pop('course_work', None)
        super().__init__(*args, **kwargs)

        if course_work:
            # Filter students who are registered for this course unit
            enrolled_students = AccessNumber.objects.filter(
                course_units__course_unit=course_work.course_unit
            ).distinct()

            self.fields['student'].queryset = enrolled_students


class StudentCourseWorkForm(forms.ModelForm):
    class Meta:
        model = get_model('StudentCourseWork')
        fields = [
            'course_work', 'status', 'submission_date',
            'hod_certified', 'hod_name', 'hod_designation',
            'hod_department', 'hod_certification_date', 'hod_signature'
        ]
        widgets = {
            'course_work': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'submission_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hod_name': forms.TextInput(attrs={'class': 'form-control'}),
            'hod_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'hod_department': forms.TextInput(attrs={'class': 'form-control'}),
            'hod_certification_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hod_signature': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, access_num=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_num = access_num

        if access_num:
            # 1. Get course units the student is registered in
            registered_course_unit_ids = access_num.course_units.values_list('course_unit__pk', flat=True)
            
            if not registered_course_unit_ids.exists():
                self.fields['course_work'].queryset = CourseWork.objects.none()
                self.fields['course_work'].empty_label = "⚠️ No course units registered"
                return

            # 2. Get ALL course works for these registered units
            all_works_for_registered_units = CourseWork.objects.filter(
                course_unit__in=registered_course_unit_ids
            )
            
            # 3. CORRECT WAY: Get ONLY course works already assigned that are in these units
            existing_works = StudentCourseWork.objects.filter(
                access_number=access_num,
                course_work__course_unit__in=registered_course_unit_ids
            ).values_list('course_work__pk', flat=True)
            
            # 4. Now exclude only relevant existing works
            available_works = all_works_for_registered_units.exclude(
                pk__in=existing_works
            )
            
            if available_works.exists():
                self.fields['course_work'].queryset = available_works
                self.fields['course_work'].empty_label = "Select Course Work"
            else:
                self.fields['course_work'].queryset = CourseWork.objects.none()
                self.fields['course_work'].empty_label = "✅ All course works already assigned"
        else:
            self.fields['course_work'].queryset = CourseWork.objects.none()
            self.fields['course_work'].empty_label = "Invalid access number"
# Formset
StudentCourseWorkFormSet = forms.inlineformset_factory(
    AccessNumber,
    StudentCourseWork,
    form=StudentCourseWorkForm,
    extra=5,
    can_delete=True,
    can_order=False
)

class AssociationForm(forms.ModelForm):
    """Form for association/club management"""
    
    class Meta:
        model = get_model('Association')
        fields = ['name', 'association_type', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'association_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }




# forms.py — FINAL — INCLUDES DoS FIELDS

# students/forms.py


class StudentAssociationForm(forms.ModelForm):
    """Form for managing student association membership — INCLUDING DoS Certification Fields"""

    class Meta:
        model = StudentAssociation
        fields = [
            'association',
            'status',
            'dos_certified',
            'dos_name',
            'dos_designation',
            'dos_department',
            'dos_certification_date',
            'dos_signature',
        ]
        widgets = {
            'association': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'dos_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dos_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'dos_department': forms.TextInput(attrs={'class': 'form-control'}),
            'dos_certification_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'dos_certified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active associations
        self.fields['association'].queryset = Association.objects.filter(is_active=True)
        # Help text for signature
        self.fields['dos_signature'].help_text = "Upload signature image (PNG, JPG)"


class BaseStudentAssociationFormSet(forms.BaseInlineFormSet):
    """Prevent duplicate association memberships"""
    def clean(self):
        super().clean()
        associations = set()
        for form in self.forms:
            if form.cleaned_data.get('DELETE') or not form.cleaned_data.get('association'):
                continue
            assoc = form.cleaned_data['association']
            if assoc in associations:
                raise ValidationError(f"You cannot add '{assoc.name}' more than once.")
            associations.add(assoc)


# Create the formset
StudentAssociationFormSet = inlineformset_factory(
    AccessNumber,
    StudentAssociation,
    form=StudentAssociationForm,
    formset=BaseStudentAssociationFormSet,
    fields=[
        'association',
        'status',
        'dos_certified',
        'dos_name',
        'dos_designation',
        'dos_department',
        'dos_certification_date',
        'dos_signature',
    ],
    extra=1,
    can_delete=True,
    widgets={
        'association': forms.Select(attrs={'class': 'form-control'}),
        'status': forms.Select(attrs={'class': 'form-control'}),
        'dos_name': forms.TextInput(attrs={'class': 'form-control'}),
        'dos_designation': forms.TextInput(attrs={'class': 'form-control'}),
        'dos_department': forms.TextInput(attrs={'class': 'form-control'}),
        'dos_certification_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        'dos_certified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)
# forms.py

from django import forms
from django.apps import apps

def get_model(model_name):
    return apps.get_model('pass_book', model_name)

class DeadSemesterApplicationForm(forms.ModelForm):
    """Form for dead semester/year applications"""
    
    class Meta:
        model = get_model('DeadSemesterApplication')
        fields = [
            'application_type', 'dead_semester', 'dead_year', 'reason',
            # HOD fields
            'hod_recommended', 'hod_name', 'hod_designation', 'hod_department', 'hod_signature', 'hod_date',
            # Faculty fields
            'faculty_recommended', 'faculty_name', 'faculty_designation', 'faculty_department', 'faculty_signature', 'faculty_date',
            # Registrar fields
            'registrar_recommended', 'registrar_name', 'registrar_designation', 'registrar_department', 'registrar_signature', 'registrar_date',
        ]
        widgets = {
            'application_type': forms.Select(attrs={'class': 'form-control'}),
            'dead_semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 2}),
            'dead_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'hod_name': forms.TextInput(attrs={'class': 'form-control'}),
            'hod_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'hod_department': forms.TextInput(attrs={'class': 'form-control'}),
            'hod_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hod_signature': forms.FileInput(attrs={'class': 'form-control'}),
            'faculty_name': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty_department': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'faculty_signature': forms.FileInput(attrs={'class': 'form-control'}),
            'registrar_name': forms.TextInput(attrs={'class': 'form-control'}),
            'registrar_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'registrar_department': forms.TextInput(attrs={'class': 'form-control'}),
            'registrar_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'registrar_signature': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
     self.mode = kwargs.pop('mode', 'full')  # 'full', 'hod', 'faculty', 'registrar'
     super().__init__(*args, **kwargs)

     if self.mode == 'hod':
        hod_fields = {'hod_recommended', 'hod_name', 'hod_designation', 'hod_department', 'hod_signature', 'hod_date'}
        for field_name in self.fields:
            if field_name not in hod_fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget = forms.HiddenInput()
            else:
                # 👇 Make sure key fields are required
                if field_name in ['hod_name', 'hod_designation', 'hod_department']:
                    self.fields[field_name].required = True

     elif self.mode == 'faculty':
        faculty_fields = {'faculty_recommended', 'faculty_name', 'faculty_designation', 'faculty_department', 'faculty_signature', 'faculty_date'}
        for field_name in self.fields:
            if field_name not in faculty_fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget = forms.HiddenInput()
            else:
                # 👇 Require these fields
                if field_name in ['faculty_name', 'faculty_designation', 'faculty_department']:
                    self.fields[field_name].required = True

     elif self.mode == 'registrar':
        registrar_fields = {'registrar_recommended', 'registrar_name', 'registrar_designation', 'registrar_department', 'registrar_signature', 'registrar_date'}
        for field_name in self.fields:
            if field_name not in registrar_fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget = forms.HiddenInput()
            else:
                if field_name in ['registrar_name', 'registrar_designation', 'registrar_department']:
                    self.fields[field_name].required = True
    def clean(self):
        cleaned_data = super().clean()
        app_type = cleaned_data.get('application_type')
        dead_semester = cleaned_data.get('dead_semester')
        dead_year = cleaned_data.get('dead_year')

        if app_type == 'SEMESTER' and not dead_semester:
            raise ValidationError("Dead semester number is required for semester applications.")
        if app_type == 'YEAR' and not dead_year:
            raise ValidationError("Dead year number is required for year applications.")
        
        return cleaned_data


class ResumptionApplicationForm(forms.ModelForm):
    """Form for resumption applications"""
    
    class Meta:
        model = ResumptionApplication
        fields = ['resume_semester', 'resume_academic_year', 'reason']
        widgets = {
            'resume_semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 2}),
            'resume_academic_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }



class MedicalRegistrationForm(forms.ModelForm):
    """Form for medical registration"""
    
    class Meta:
        model = MedicalRegistration
        fields = ['medical_officer_name', 'medical_officer_signature']
        widgets = {
            'medical_officer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter medical officer name',
                'maxlength': 200
            }),
            'medical_officer_signature': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make medical officer name required
        self.fields['medical_officer_name'].required = True
        
        # Add help text
        self.fields['medical_officer_signature'].help_text = 'Upload signature image (PNG, JPG, etc.)'
    
    def clean_medical_officer_name(self):
        """Clean and validate medical officer name"""
        name = self.cleaned_data.get('medical_officer_name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError("Medical officer name must be at least 2 characters long.")
        return name
    
    def clean_medical_officer_signature(self):
        """Validate signature file"""
        signature = self.cleaned_data.get('medical_officer_signature')
        if signature:
            # Check file size (limit to 5MB)
            if signature.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError("Signature file size must be less than 5MB.")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if signature.content_type not in allowed_types:
                raise forms.ValidationError("Only image files (JPEG, PNG, GIF) are allowed.")
        
        return signature




class BbalaLaptopSchemeForm(forms.ModelForm):
    """Form for Bbala laptop scheme management"""
    
    class Meta:
        model = get_model('BbalaLaptopScheme')
        fields = ['laptop_serial_number', 'payment_made', 'comments']
        widgets = {
            'laptop_serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_made': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_payment_made(self):
        payment = self.cleaned_data['payment_made']
        if payment < 0:
            raise ValidationError("Payment amount cannot be negative.")
        if payment > 1500000:
            raise ValidationError("Payment cannot exceed the total cost of UGX 1,500,000.")
        return payment

'''
class MedicalRegistrationForm(forms.ModelForm):
    """Form for medical registration"""
    
    class Meta:
        model = get_model('MedicalRegistration')
        fields = ['medical_officer_name', 'medical_officer_signature']
        widgets = {
            'medical_officer_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
'''

class NCHERegistrationForm(forms.ModelForm):
    """Form for NCHE registration"""
    
    class Meta:
        model = get_model('NCHERegistration')
        fields = ['officer_name', 'officer_signature']
        widgets = {
            'officer_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

######INTERNSHIP
'''
class InternshipForm(forms.ModelForm):
    """Form for internship management"""
    
    class Meta:
        model = get_model('Internship')
        fields = [
            'status', 'company_name', 'start_date', 'end_date',
            'supervisor_name', 'supervisor_contact'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'supervisor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisor_contact': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("End date must be after start date.")
        return cleaned_data
'''

class InternshipForm(forms.ModelForm):
    """Form for internship management"""
    
    class Meta:
        model = Internship
        fields = [
            'status', 'company_name', 'start_date', 'end_date',
            'supervisor_name', 'supervisor_contact'
        ]
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'supervisor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supervisor name'
            }),
            'supervisor_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number or email'
            }),
        }
        labels = {
            'status': 'Internship Status',
            'company_name': 'Company Name',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'supervisor_name': 'Supervisor Name',
            'supervisor_contact': 'Supervisor Contact',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        status = cleaned_data.get('status')
        company_name = cleaned_data.get('company_name')
        
        # If status is DONE, require company details
        if status == 'DONE':
            if not company_name:
                raise ValidationError("Company name is required when status is 'Done'.")
            if not start_date:
                raise ValidationError("Start date is required when status is 'Done'.")
            if not end_date:
                raise ValidationError("End date is required when status is 'Done'.")
        
        # Validate date range
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("End date must be after start date.")
        
        return cleaned_data


class StudentSearchForm(forms.Form):
    """Form for searching students"""
    
    STATUS_CHOICES = [
        ('', 'All Students'),
        ('HAS_INTERNSHIP', 'Has Internship'),
        ('NO_INTERNSHIP', 'No Internship'),
        ('DONE', 'Internship Done'),
        ('NOT_DONE', 'Internship Not Done'),
    ]
    
    YEAR_CHOICES = [
        ('', 'All Years'),
        (1, 'Year 1'),
        (2, 'Year 2'),
        (3, 'Year 3'),
        (4, 'Year 4'),
        (5, 'Year 5'),
    ]
    
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by access number, name, or email...',
            'autocomplete': 'off'
        }),
        label='Search'
    )
    
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=False,
        empty_label='All Academic Years',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        label='Academic Year'
    )
    
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        required=False,
        empty_label='All Semesters',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        label='Semester'
    )
    
    year_of_study = forms.ChoiceField(
        choices=YEAR_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        label='Year of Study'
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        label='Internship Status'
    )


class QuickStudentSelectForm(forms.Form):
    """Form for quick student selection"""
    
    access_number = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter student access number...',
            'list': 'students-list',
            'autocomplete': 'off',
            'id': 'student-search-input'
        }),
        label='Student Access Number'
    )
    
    def clean_access_number(self):
        access_number = self.cleaned_data['access_number']
        
        try:
            from .models import AccessNumber
            access_num = AccessNumber.objects.get(
                access_number=access_number, 
                is_active=True
            )
            return access_number
        except AccessNumber.DoesNotExist:
            raise ValidationError("Invalid access number or student not found.")


class InternshipFilterForm(forms.Form):
    """Form for filtering internship list"""
    
    STATUS_CHOICES = [('', 'All Status')] + Internship.STATUS_CHOICES
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by student, company, or supervisor...'
        }),
        label='Search'
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        label='Status'
    )
    
    year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=False,
        empty_label='All Years',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        label='Academic Year'
    )


#####SEMESTER CLEARANCE
class SemesterClearanceForm(forms.ModelForm):
    """Form for semester clearance"""
    
    class Meta:
        model = get_model('SemesterClearance')
        fields = [
            'finance_cleared', 'finance_officer_name', 'finance_officer_designation',
            'finance_clearance_date', 'finance_signature',
            'academic_cleared', 'academic_officer_name', 'academic_officer_designation',
            'academic_clearance_date', 'academic_signature'
        ]
        widgets = {
            'finance_officer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'finance_officer_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'finance_clearance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'academic_officer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_officer_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_clearance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }



class FinanceClearanceForm(forms.ModelForm):
    class Meta:
        model = SemesterClearance
        fields = [
            'finance_cleared',
            'finance_officer_name',
            'finance_officer_designation',
            'finance_clearance_date',
            'finance_signature'
        ]
        widgets = {
            'finance_clearance_date': forms.DateInput(attrs={'type': 'date'}),
        }

class AcademicClearanceForm(forms.ModelForm):
    class Meta:
        model = SemesterClearance
        fields = [
            'academic_cleared',
            'academic_officer_name',
            'academic_officer_designation',
            'academic_clearance_date',
            'academic_signature'
        ]
        widgets = {
            'academic_clearance_date': forms.DateInput(attrs={'type': 'date'}),
        }


from django import forms
from pass_book.models import GraduationClearance  # Replace with your actual app name

class GraduationClearanceForm(forms.ModelForm):
    """Form for graduation clearance"""
    
    class Meta:
        model = GraduationClearance  # Direct model reference instead of get_model
        fields = [
            'all_requirements_met', 'clearance_date', 'approving_officer_name',
            'approving_officer_designation', 'approving_officer_signature'
        ]
        widgets = {
            'clearance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'approving_officer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'approving_officer_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'approving_officer_signature': forms.FileInput(attrs={'class': 'form-control'}),  # Added widget for signature
        }


class GraduationClearanceSearchForm(forms.Form):
    """Form for searching and filtering graduation clearances"""
    
    CLEARANCE_STATUS_CHOICES = [
        ('', 'All Status'),
        ('cleared', 'Cleared'),
        ('pending', 'Pending'),
    ]
    
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by student name, registration number, officer name...'
        })
    )
    
    status = forms.ChoiceField(
        choices=CLEARANCE_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    program = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="All Programs",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    year = forms.ChoiceField(
        choices=[],  # Will be populated in __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        # Get programs and years from kwargs
        programs = kwargs.pop('programs', None)
        years = kwargs.pop('years', None)
        
        super().__init__(*args, **kwargs)
        
        # Set program queryset
        if programs:
            self.fields['program'].queryset = programs
        
        # Set year choices
        if years:
            year_choices = [('', 'All Years')] + [(year, str(year)) for year in years]
            self.fields['year'].choices = year_choices


class BulkClearanceActionForm(forms.Form):
    """Form for bulk actions on graduation clearances"""
    
    ACTION_CHOICES = [
        ('', 'Select Action...'),
        ('create_clearances', 'Create Clearances'),
        ('mark_cleared', 'Mark as Cleared'),
        ('mark_pending', 'Mark as Pending'),
        ('export_csv', 'Export to CSV'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'bulkAction'
        })
    )
    
    student_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def clean_student_ids(self):
        """Convert comma-separated student IDs to list"""
        student_ids_str = self.cleaned_data.get('student_ids', '')
        
        if not student_ids_str:
            raise ValidationError("No students selected.")
        
        try:
            # Split by comma and convert to list of UUIDs
            student_ids = [id.strip() for id in student_ids_str.split(',') if id.strip()]
            
            if not student_ids:
                raise ValidationError("No valid student IDs provided.")
            
            return student_ids
            
        except Exception as e:
            raise ValidationError(f"Invalid student ID format: {str(e)}")
    
    def clean(self):
        """Validate the form"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        student_ids = cleaned_data.get('student_ids')
        
        if action and not student_ids:
            raise ValidationError("Please select at least one student to perform the action.")
        
        return cleaned_data

#####Still in graduation forms


# forms.py
class StudentSearchForm(forms.Form):
    """Form for searching students"""
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, registration number, or access number'
        })
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Program"
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Academic Year"
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Semester"
    )
# Formsets for bulk operations
StudentCourseUnitFormSet = inlineformset_factory(
    AccessNumber, StudentCourseUnit, form=StudentCourseUnitForm, extra=0, can_delete=True
)

StudentCourseWorkFormSet = inlineformset_factory(
    AccessNumber, StudentCourseWork, form=StudentCourseWorkForm, extra=0, can_delete=True
)




