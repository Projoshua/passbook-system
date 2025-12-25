# views.py loaded at 1732651200.0
# Standard library imports
import json
import logging
import os
import time
from datetime import datetime
# Django core imports
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models, DatabaseError, connection, transaction
from django.db.models import Q, Count, Sum, F, Value, When, Case, BooleanField, Exists, OuterRef, Prefetch
from django.forms import inlineformset_factory
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView
)
# Local app imports
from .models import (
    Student, AcademicYear, Semester, AccessNumber, SemesterRegistration,
    CourseUnit, StudentCourseUnit, CourseWork, StudentCourseWork,
    Association, StudentAssociation, DeadSemesterApplication,
    ResumptionApplication, BbalaLaptopScheme, MedicalRegistration,
    NCHERegistration, Internship, SemesterClearance, GraduationClearance,
    Program, Course
)
from .forms import (
    StudentForm, AcademicYearForm, SemesterForm,
    SemesterRegistrationForm, CourseUnitForm, StudentCourseUnitForm,
    CourseWorkForm, StudentCourseWorkForm, AssociationForm,
    StudentAssociationForm, DeadSemesterApplicationForm,
    ResumptionApplicationForm, BbalaLaptopSchemeForm, MedicalRegistrationForm,
    NCHERegistrationForm, InternshipForm, SemesterClearanceForm,
    GraduationClearanceForm, StudentSearchForm, StudentCourseUnitFormSet,
    StudentCourseWorkFormSet, StudentAssociationFormSet,
    AssignCourseWorkForm, AcademicClearanceForm, FinanceClearanceForm,
    GenerateAccessNumberForm, BulkGenerateAccessNumberForm, ProgramForm, CourseForm
)
logger = logging.getLogger(__name__)

def get_form(form_name):
    try:
        # Dynamically import from forms module
        from . import forms
        return getattr(forms, form_name, None)
    except ImportError:
        return None

#==========================================================
#PROGRAM AND COURSE VIEWS
#=========================================================

# Add these view classes to your views.py
class ProgramListView(LoginRequiredMixin, ListView):
    """List all programs"""
    model = Program
    template_name = 'student_registration/program_list.html'
    context_object_name = 'programs'
    paginate_by = 20

class ProgramCreateView(LoginRequiredMixin, CreateView):
    """Create a new program"""
    model = Program
    form_class = get_form("ProgramForm")
    template_name = 'student_registration/program_form.html'
    success_url = reverse_lazy('pass_book:program_list')

class ProgramUpdateView(LoginRequiredMixin, UpdateView):
    """Update a program"""
    model = Program
    form_class = get_form("ProgramForm")
    template_name = 'student_registration/program_form.html'
    success_url = reverse_lazy('pass_book:program_list')

class ProgramDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a program"""
    model = Program
    template_name = 'student_registration/program_confirm_delete.html'
    success_url = reverse_lazy('pass_book:program_list')

# COURSE VIEWS
class CourseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all courses"""
    model = Course
    template_name = 'student_registration/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin

class CourseCreateView(LoginRequiredMixin, CreateView): # Consider adding UserPassesTestMixin
    """Create a new course"""
    model = Course
    form_class = get_form("CourseForm")
    template_name = 'student_registration/course_form.html'
    success_url = reverse_lazy('pass_book:course_list')
    # Add test_func if you want only HOD/sysadmin
    def test_func(self):
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin

class CourseUpdateView(LoginRequiredMixin, UpdateView): # Consider adding UserPassesTestMixin
    """Update a course"""
    model = Course
    form_class = get_form("CourseForm")
    template_name = 'student_registration/course_form.html'
    success_url = reverse_lazy('pass_book:course_list')
    # Add test_func if you want only HOD/sysadmin
    def test_func(self):
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin

class CourseDeleteView(LoginRequiredMixin, DeleteView): # Consider adding UserPassesTestMixin
    """Delete a course"""
    model = Course
    template_name = 'student_registration/course_confirm_delete.html'
    success_url = reverse_lazy('pass_book:course_list')
    # Add test_func if you want only HOD/sysadmin
    def test_func(self):
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin

# ============================================================================
# DASHBOARD AND OVERVIEW VIEWS
# ============================================================================

@login_required
def dashboard_view(request):
    """Main dashboard with statistics and overview"""
    context = {
        'total_students': Student.objects.count(),
        'active_access_numbers': AccessNumber.objects.filter(is_active=True).count(),
        'active_academic_years': AcademicYear.objects.filter(is_active=True).count(),
        'active_semesters': Semester.objects.filter(is_active=True).count(),
        'total_course_units': CourseUnit.objects.filter(is_active=True).count(),
        'total_associations': Association.objects.filter(is_active=True).count(),
        'pending_dead_semester_apps': DeadSemesterApplication.objects.annotate(
            is_approved=Case(
                When(
                    hod_recommended=True,
                    faculty_recommended=True,
                    registrar_recommended=True,
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(is_approved=False).count(),
        'laptop_scheme_participants': BbalaLaptopScheme.objects.count(),
        'recent_registrations': SemesterRegistration.objects.select_related(
            'access_number__student'
        ).order_by('-created_at')[:5],
        'recent_clearances': SemesterClearance.objects.select_related(
            'access_number__student'
        ).order_by('-created_at')[:5]
    }
    return render(request, 'student_registration/dashboard.html', context)

# ============================================================================
# STUDENT VIEWS
# ============================================================================

# In your views.py file, add this line:
from django.db import IntegrityError, transaction

class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'student_registration/student_form.html'
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            kwargs.update({
                'files': self.request.FILES
            })
        return kwargs
    
    def form_valid(self, form):
        # Copy program code to student
        form.instance.program_code = form.instance.program.code
        
        # Calculate expected graduation year
        form.instance.expected_graduation_year = (
            form.instance.admission_year + form.instance.program.duration
        )
        
        messages.success(
            self.request, 
            f"Student {form.instance.name} registered successfully with registration number: {form.instance.registration_number}"
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

from django.db import transaction, IntegrityError  # Added IntegrityError import
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import render, redirect


from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import StudentForm
from .models import Student

from django.shortcuts import render, get_object_or_404
from django.views import View
from .models import (
    Student, AccessNumber, SemesterRegistration, StudentCourseUnit, 
    StudentCourseWork, StudentAssociation, DeadSemesterApplication,
    ResumptionApplication, BbalaLaptopScheme, MedicalRegistration,
    NCHERegistration, Internship, SemesterClearance, GraduationClearance,
    Program, CourseUnit, Course, Association, Semester, AcademicYear
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.contrib import messages
from pass_book.models import (
    Student, AccessNumber, SemesterRegistration, StudentCourseUnit,
    StudentCourseWork, StudentAssociation, DeadSemesterApplication,
    ResumptionApplication, BbalaLaptopScheme, MedicalRegistration,
    NCHERegistration, Internship, SemesterClearance, GraduationClearance
)


class StudentDetailsView(LoginRequiredMixin, View):
    """View to display all data about a single student"""
    template_name = 'student_registration/student_detail.html'
    
    def get(self, request, student_id=None):
        # If no student_id provided and user is a student, show their own profile
        if student_id is None:
            if request.user.is_student and hasattr(request.user, 'student_profile'):
                student = request.user.student_profile
            else:
                messages.error(request, "No student profile found.")
                return redirect('pass_book:dashboard-passbook')
        else:
            # Get student by UUID or registration number
            try:
                student = get_object_or_404(Student, pk=student_id)
            except:
                # Try by registration number if UUID fails
                student = get_object_or_404(Student, registration_number=student_id)
            
            # Permission check: students can only view their own profile
            if request.user.is_student:
                if not hasattr(request.user, 'student_profile') or request.user.student_profile.id != student.id:
                    messages.error(request, "You can only view your own profile.")
                    return redirect('pass_book:student_details', student_id=request.user.student_profile.id)
            # Staff can view any student (check permissions)
            elif not request.user.has_perm('pass_book.view_student'):
                messages.error(request, "You don't have permission to view student details.")
                return redirect('pass_book:dashboard-passbook')
        
        # Get all related data with optimized queries
        access_numbers = AccessNumber.objects.filter(
            student=student
        ).select_related('academic_year', 'semester').order_by('-academic_year__start_date', '-semester__number')
        
        # Get semester registrations for each access number
        semester_registrations = SemesterRegistration.objects.filter(
            access_number__student=student
        ).select_related(
            'access_number',
            'access_number__academic_year',
            'access_number__semester'
        ).order_by('-access_number__academic_year__start_date', '-access_number__semester__number')
        
        # Get all course units across all semesters
        student_course_units = StudentCourseUnit.objects.filter(
            access_number__student=student
        ).select_related(
            'access_number',
            'access_number__academic_year',
            'access_number__semester',
            'course_unit'
        ).order_by('-access_number__academic_year__start_date', 'course_unit__code')
        
        # Get all course works
        student_course_works = StudentCourseWork.objects.filter(
            access_number__student=student
        ).select_related(
            'access_number',
            'course_work',
            'course_work__course_unit'
        ).order_by('-access_number__academic_year__start_date', 'course_work__title')
        
        # Get associations
        student_associations = StudentAssociation.objects.filter(
            access_number__student=student
        ).select_related(
            'access_number',
            'association'
        ).order_by('association__name')
        
        # Get dead semester applications
        dead_semester_apps = DeadSemesterApplication.objects.filter(
            student=student
        ).order_by('-application_date')
        
        # Get resumption applications
        resumption_apps = ResumptionApplication.objects.filter(
            dead_semester_application__student=student
        ).select_related('dead_semester_application').order_by('-application_date')
        
        # Get other related records
        laptop_scheme = BbalaLaptopScheme.objects.filter(student=student).first()
        
        # Get medical registrations for all access numbers
        medical_registrations = MedicalRegistration.objects.filter(
            access_number__student=student
        ).select_related('access_number').order_by('-registration_date')
        
        # Get NCHE registrations
        nche_registrations = NCHERegistration.objects.filter(
            access_number__student=student
        ).select_related('access_number').order_by('-registration_date')
        
        # Get internship records
        internships = Internship.objects.filter(
            access_number__student=student
        ).select_related('access_number').order_by('-start_date')
        
        # Get semester clearances
        semester_clearances = SemesterClearance.objects.filter(
            access_number__student=student
        ).select_related('access_number').order_by('-created_at')
        
        # Get graduation clearance
        graduation_clearance = GraduationClearance.objects.filter(student=student).first()
        
        # Get program details
        program = student.program
        
        # Group course units by semester
        course_units_by_semester = {}
        for scu in student_course_units:
            semester_key = f"{scu.access_number.academic_year.year_label} - {scu.access_number.semester.get_number_display()}"
            if semester_key not in course_units_by_semester:
                course_units_by_semester[semester_key] = []
            course_units_by_semester[semester_key].append(scu)
        
        # Group course works by semester
        course_works_by_semester = {}
        for scw in student_course_works:
            semester_key = f"{scw.access_number.academic_year.year_label} - {scw.access_number.semester.get_number_display()}"
            if semester_key not in course_works_by_semester:
                course_works_by_semester[semester_key] = []
            course_works_by_semester[semester_key].append(scw)
        
        # Group access numbers by academic year
        access_numbers_by_year = {}
        for an in access_numbers:
            year = an.academic_year.year_label
            if year not in access_numbers_by_year:
                access_numbers_by_year[year] = []
            access_numbers_by_year[year].append(an)
        
        context = {
            'student': student,
            'program': program,
            'access_numbers': access_numbers,
            'access_numbers_by_year': access_numbers_by_year,
            'semester_registrations': semester_registrations,
            'student_course_units': student_course_units,
            'course_units_by_semester': course_units_by_semester,
            'student_course_works': student_course_works,
            'course_works_by_semester': course_works_by_semester,
            'student_associations': student_associations,
            'dead_semester_apps': dead_semester_apps,
            'resumption_apps': resumption_apps,
            'laptop_scheme': laptop_scheme,
            'medical_registrations': medical_registrations,
            'nche_registrations': nche_registrations,
            'internships': internships,
            'semester_clearances': semester_clearances,
            'graduation_clearance': graduation_clearance,
            
            # Statistics
            'total_course_units': student_course_units.count(),
            'passed_course_units': student_course_units.filter(status='PASSED').count(),
            'total_course_works': student_course_works.count(),
            'completed_course_works': student_course_works.filter(status='DONE').count(),
            'active_associations': student_associations.filter(status='ACTIVE').count(),
            
            # Status colors
            'session_choices': dict(Student.SESSION_CHOICES),
            'status_colors': {
                'PASSED': 'success',
                'MISSED': 'danger',
                'RETAKE': 'warning',
                'DONE': 'success',
                'NOT_DONE': 'danger',
                'ACTIVE': 'success',
                'INACTIVE': 'secondary',
            },
            
            # View mode
            'is_own_profile': request.user.is_student and hasattr(request.user, 'student_profile') and request.user.student_profile.id == student.id,
        }
        
        return render(request, self.template_name, context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Student, Program
from datetime import datetime

'''
@login_required
def student_create(request):
    """
    Function-based view for creating a new student.
    Registration number is manually entered by the user.
    Static access number is auto-generated on save.
    """
    programs = Program.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                name = request.POST.get('name')
                program_id = request.POST.get('program')
                nationality = request.POST.get('nationality')
                student_contact = request.POST.get('student_contact')
                
                # Optional parent/guardian fields
                parent_guardian_name = request.POST.get('parent_guardian_name', '')
                parent_guardian_contact = request.POST.get('parent_guardian_contact', '')
                
                # Academic info
                admission_year = request.POST.get('admission_year')
                session = request.POST.get('session')
                expected_graduation_year = request.POST.get('expected_graduation_year', None)
                
                # MANUAL REGISTRATION NUMBER - User enters this
                registration_number = request.POST.get('registration_number')
                
                # Manual receipt info
                manual_received = request.POST.get('manual_received') == 'on'
                manual_received_date = request.POST.get('manual_received_date', None)
                
                # File uploads
                student_photo = request.FILES.get('student_photo')
                parent_guardian_photo = request.FILES.get('parent_guardian_photo')
                signature = request.FILES.get('signature')
                parent_guardian_signature = request.FILES.get('parent_guardian_signature')
                
                # Validation
                if not all([name, program_id, nationality, student_contact, 
                           admission_year, session, registration_number]):
                    messages.error(request, 'Please fill in all required fields.')
                    return render(request, 'student_registration/student_create.html', {
                        'programs': programs
                    })
                
                # Check if registration number already exists
                if Student.objects.filter(registration_number=registration_number).exists():
                    messages.error(request, f'Registration number {registration_number} already exists.')
                    return render(request, 'student_registration/student_create.html', {
                        'programs': programs
                    })
                
                # Get program
                program = get_object_or_404(Program, id=program_id)
                
                # Create student - static_access_number will be auto-generated in save()
                student = Student(
                    name=name,
                    program=program,
                    nationality=nationality,
                    student_contact=student_contact,
                    parent_guardian_name=parent_guardian_name,
                    parent_guardian_contact=parent_guardian_contact,
                    admission_year=int(admission_year),
                    session=session,
                    registration_number=registration_number,  # Manual input
                    manual_received=manual_received,
                )
                
                # Add optional fields
                if expected_graduation_year:
                    student.expected_graduation_year = int(expected_graduation_year)
                
                if manual_received_date:
                    student.manual_received_date = manual_received_date
                
                # Add file uploads
                if student_photo:
                    student.student_photo = student_photo
                if parent_guardian_photo:
                    student.parent_guardian_photo = parent_guardian_photo
                if signature:
                    student.signature = signature
                if parent_guardian_signature:
                    student.parent_guardian_signature = parent_guardian_signature
                
                # Save student - this triggers static_access_number generation
                student.save()
                
                messages.success(
                    request, 
                    f'Student {student.name} created successfully! '
                    f'Static Access Number: {student.static_access_number}'
                )
                return redirect('pass_book:student_list')  # Adjust URL name as needed
                
        except Exception as e:
            messages.error(request, f'Error creating student: {str(e)}')
            return render(request, 'student_registration/student_create.html', {
                'programs': programs
            })
    
    # GET request - show form
    context = {
        'programs': programs,
        'current_year': datetime.now().year,
        'session_choices': Student.SESSION_CHOICES,
    }
    return render(request, 'student_registration/student_create.html', context)
'''


from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, Program

'''
@login_required
def student_create(request):
    """
    Function-based view for creating a new student.
    Registration number is manually entered by the user.
    Static access number is auto-generated on save.
    User account is automatically created with static_access_number as username and '123' as password.
    """
    programs = Program.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                name = request.POST.get('name')
                program_id = request.POST.get('program')
                nationality = request.POST.get('nationality')
                student_contact = request.POST.get('student_contact')
                
                # Optional parent/guardian fields
                parent_guardian_name = request.POST.get('parent_guardian_name', '')
                parent_guardian_contact = request.POST.get('parent_guardian_contact', '')
                
                # Academic info
                admission_year = request.POST.get('admission_year')
                session = request.POST.get('session')
                expected_graduation_year = request.POST.get('expected_graduation_year', None)
                
                # MANUAL REGISTRATION NUMBER - User enters this
                registration_number = request.POST.get('registration_number')
                
                # Manual receipt info
                manual_received = request.POST.get('manual_received') == 'on'
                manual_received_date = request.POST.get('manual_received_date', None)
                
                # File uploads
                student_photo = request.FILES.get('student_photo')
                parent_guardian_photo = request.FILES.get('parent_guardian_photo')
                signature = request.FILES.get('signature')
                parent_guardian_signature = request.FILES.get('parent_guardian_signature')
                
                # Validation
                if not all([name, program_id, nationality, student_contact, 
                           admission_year, session, registration_number]):
                    messages.error(request, 'Please fill in all required fields.')
                    return render(request, 'student_registration/student_create.html', {
                        'programs': programs
                    })
                
                # Check if registration number already exists
                if Student.objects.filter(registration_number=registration_number).exists():
                    messages.error(request, f'Registration number {registration_number} already exists.')
                    return render(request, 'student_registration/student_create.html', {
                        'programs': programs
                    })
                
                # Get program
                program = get_object_or_404(Program, id=program_id)
                
                # Create student - static_access_number and user account will be auto-generated
                student = Student(
                    name=name,
                    program=program,
                    nationality=nationality,
                    student_contact=student_contact,
                    parent_guardian_name=parent_guardian_name,
                    parent_guardian_contact=parent_guardian_contact,
                    admission_year=int(admission_year),
                    session=session,
                    registration_number=registration_number,
                    manual_received=manual_received,
                )
                
                # Add optional fields
                if expected_graduation_year:
                    student.expected_graduation_year = int(expected_graduation_year)
                
                if manual_received_date:
                    student.manual_received_date = manual_received_date
                
                # Add file uploads
                if student_photo:
                    student.student_photo = student_photo
                if parent_guardian_photo:
                    student.parent_guardian_photo = parent_guardian_photo
                if signature:
                    student.signature = signature
                if parent_guardian_signature:
                    student.parent_guardian_signature = parent_guardian_signature
                
                # Save student - this triggers static_access_number and user account generation
                student.save()
                
                messages.success(
                    request, 
                    f'Student {student.name} created successfully! '
                    f'Static Access Number: {student.static_access_number} | '
                    f'Login Username: {student.static_access_number} | '
                    f'Default Password: 123'
                )
                return redirect('pass_book:student_list')
                
        except Exception as e:
            messages.error(request, f'Error creating student: {str(e)}')
            return render(request, 'student_registration/student_create.html', {
                'programs': programs
            })
    
    # GET request - show form
    context = {
        'programs': programs,
        'current_year': datetime.now().year,
        'session_choices': Student.SESSION_CHOICES,
    }
    return render(request, 'student_registration/student_create.html', context)
'''


from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, Program


@login_required
def student_create(request):
    """
    Function-based view for creating a new student.
    Registration number is manually entered by the user.
    Static access number is auto-generated on save.
    User account is automatically created with static_access_number as username and '123' as password.
    """
    programs = Program.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                name = request.POST.get('name')
                program_id = request.POST.get('program')
                nationality = request.POST.get('nationality')
                student_contact = request.POST.get('student_contact')
                
                # Optional parent/guardian fields
                parent_guardian_name = request.POST.get('parent_guardian_name', '')
                parent_guardian_contact = request.POST.get('parent_guardian_contact', '')
                
                # Academic info
                admission_year = request.POST.get('admission_year')
                session = request.POST.get('session')
                expected_graduation_year = request.POST.get('expected_graduation_year', None)
                
                # MANUAL REGISTRATION NUMBER - User enters this
                registration_number = request.POST.get('registration_number')
                
                # Manual receipt info
                manual_received = request.POST.get('manual_received') == 'on'
                manual_received_date = request.POST.get('manual_received_date', None)
                
                # File uploads
                student_photo = request.FILES.get('student_photo')
                parent_guardian_photo = request.FILES.get('parent_guardian_photo')
                signature = request.FILES.get('signature')
                parent_guardian_signature = request.FILES.get('parent_guardian_signature')
                
                # Validation
                if not all([name, program_id, nationality, student_contact, 
                           admission_year, session, registration_number]):
                    messages.error(request, 'Please fill in all required fields.')
                    return render(request, 'student_registration/student_create.html', {
                        'programs': programs
                    })
                
                # Check if registration number already exists
                if Student.objects.filter(registration_number=registration_number).exists():
                    messages.error(request, f'Registration number {registration_number} already exists.')
                    return render(request, 'student_registration/student_create.html', {
                        'programs': programs
                    })
                
                # Get program
                program = get_object_or_404(Program, id=program_id)
                
                # Create student - static_access_number and user account will be auto-generated
                student = Student(
                    name=name,
                    program=program,
                    nationality=nationality,
                    student_contact=student_contact,
                    parent_guardian_name=parent_guardian_name,
                    parent_guardian_contact=parent_guardian_contact,
                    admission_year=int(admission_year),
                    session=session,
                    registration_number=registration_number,
                    manual_received=manual_received,
                )
                
                # Add optional fields
                if expected_graduation_year:
                    student.expected_graduation_year = int(expected_graduation_year)
                
                if manual_received_date:
                    student.manual_received_date = manual_received_date
                
                # Add file uploads
                if student_photo:
                    student.student_photo = student_photo
                if parent_guardian_photo:
                    student.parent_guardian_photo = parent_guardian_photo
                if signature:
                    student.signature = signature
                if parent_guardian_signature:
                    student.parent_guardian_signature = parent_guardian_signature
                
                # Save student - this triggers static_access_number generation
                student.save()
                
                # IMPORTANT: Explicitly create user account if not created
                if not student.user:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    
                    user = User.objects.create_user(
                        username=student.static_access_number,
                        password='123',
                        user_type='student',
                        first_name=student.name.split()[0] if student.name else '',
                        last_name=' '.join(student.name.split()[1:]) if len(student.name.split()) > 1 else '',
                        email=f'{student.static_access_number}@slau.ac.ug'
                    )
                    user.is_active = True
                    user.save()
                    
                    student.user = user
                    student.save(update_fields=['user'])
                
                messages.success(
                    request, 
                    f'Student {student.name} created successfully! '
                    f'Static Access Number: {student.static_access_number} | '
                    f'Login Username: {student.static_access_number} | '
                    f'Default Password: 123'
                )
                return redirect('pass_book:student_list')
                
        except Exception as e:
            messages.error(request, f'Error creating student: {str(e)}')
            return render(request, 'student_registration/student_create.html', {
                'programs': programs
            })
    
    # GET request - show form
    context = {
        'programs': programs,
        'current_year': datetime.now().year,
        'session_choices': Student.SESSION_CHOICES,
    }
    return render(request, 'student_registration/student_create.html', context)




@login_required
def student_list(request):
    """List all students with their details"""
    students = Student.objects.select_related('program').all()
    context = {
        'students': students
    }
    return render(request, 'student_registration/student_list.html', context)














class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'student_registration/student_form.html'
    success_url = reverse_lazy('pass_book:student_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Student updated successfully.")
        return super().form_valid(form)


class StudentDetailView(DetailView):
    model = Student
    template_name = 'student_registration/student_detail.html'
    context_object_name = 'student'


class StudentDeleteView(DeleteView):
    model = Student
    template_name = 'student_registration/student_confirm_delete.html'
    success_url = reverse_lazy('pass_book:student_list')
    
    def delete(self, request, *args, **kwargs):
        # Allow Sysadmin, Academic Registrar, or HOD to delete students
        if not (request.user.is_academic_registrar or request.user.is_head_of_department or request.user.is_sysadmin):
            raise PermissionDenied("Only Academic Registrar, Head of Department, or System Administrator can delete students.")
        messages.success(request, "Student deleted successfully.")
        return super().delete(request, *args, **kwargs)


class StudentListView(ListView):
    model = Student
    template_name = 'student_registration/student_list.html'
    context_object_name = 'students'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Student.objects.all().select_related('program')
        search_query = self.request.GET.get('q', '').strip()
        program_code = self.request.GET.get('program', '').strip()

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(registration_number__icontains=search_query)
                | Q(static_access_number__icontains=search_query)
            )

        if program_code:
            queryset = queryset.filter(program__code=program_code)

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # For filters in template
        context['programs'] = Program.objects.all().order_by('code')
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['selected_program'] = self.request.GET.get('program', '').strip()
        return context
# ============================================================================
# ACADEMIC YEAR AND SEMESTER VIEWS
# ============================================================================
class AcademicYearListView(LoginRequiredMixin, ListView):
    model = AcademicYear
    template_name = 'student_registration/academic_year_list.html'
    context_object_name = 'academic_years'
    def get_queryset(self):
        try:
            queryset = AcademicYear.objects.all()
            test_result = list(queryset[:1])
            logger.info(f"Found {len(test_result)} academic years in database")
            return queryset.order_by('-start_date')
        except DatabaseError as e:
            logger.error(f"DatabaseError in AcademicYearListView: {str(e)}")
            return AcademicYear.objects.none()
        except Exception as e:
            logger.error(f"Unexpected error in AcademicYearListView: {str(e)}")
            return AcademicYear.objects.none()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            try:
                active_year = AcademicYear.objects.filter(is_active=True).first()
                context['active_academic_year'] = active_year
                logger.info(f"Active academic year: {active_year}")
            except DatabaseError as e:
                logger.error(f"Error getting active academic year: {str(e)}")
                context['active_academic_year'] = None
                context['db_query_error'] = True
        except DatabaseError as e:
            logger.error(f"Database connection failed: {str(e)}")
            context['database_error'] = True
            context['connection_error'] = True
            context['active_academic_year'] = None
        except Exception as e:
            logger.error(f"Unexpected error in context: {str(e)}")
            context['database_error'] = True
            context['active_academic_year'] = None
        return context

class AcademicYearUpdateView(LoginRequiredMixin, UpdateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'student_registration/academic_year_form.html'
    success_url = reverse_lazy('pass_book:academic_year_list')
    def form_valid(self, form):
        messages.success(self.request, 'Academic year updated successfully!')
        return super().form_valid(form)

class AcademicYearDeleteView(LoginRequiredMixin, DeleteView):
    model = AcademicYear
    success_url = reverse_lazy('pass_book:academic_year_list')
    template_name = 'student_registration/academic_year_confirm_delete.html'
    def delete(self, request, *args, **kwargs):
        # Allow Sysadmin or Academic Registrar to delete academic years
        if not (request.user.is_academic_registrar or request.user.is_sysadmin):
            raise PermissionDenied("Only Academic Registrar or System Administrator can delete academic years.")
        messages.success(request, 'Academic year deleted successfully!')
        return super().delete(request, *args, **kwargs)

def academic_year_set_active(request, pk):
    # Allow Sysadmin or Academic Registrar to set active year
    if not (request.user.is_academic_registrar or request.user.is_sysadmin):
         raise PermissionDenied("Only Academic Registrar or System Administrator can set the active academic year.")
    if request.method == 'POST':
        academic_year = get_object_or_404(AcademicYear, pk=pk)
        AcademicYear.objects.filter(is_active=True).update(is_active=False)
        academic_year.is_active = True
        academic_year.save()
        messages.success(request, f'{academic_year.year_label} is now the active academic year!')
    return redirect('academic_year_list')


class AcademicYearCreateView(LoginRequiredMixin, CreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'student_registration/academic_year_form.html'
    success_url = reverse_lazy('pass_book:academic_year_list')
    
    def form_valid(self, form):
        # ✅ FIXED: Changed 'request.user' to 'self.request.user'
        if not (self.request.user.is_academic_registrar or self.request.user.is_sysadmin or self.request.user.is_head_of_department):
            messages.error(self.request, "Only Academic Registrar or System Administrator can create academic years.")
            return self.form_invalid(form)
        
        try:
            if form.cleaned_data.get('is_active'):
                AcademicYear.objects.filter(is_active=True).update(is_active=False)
            response = super().form_valid(form)
            messages.success(self.request, 'Academic year created successfully!')
            return response
        except DatabaseError as e:
            messages.error(
                self.request,
                'Database error occurred while creating academic year. Please try again.'
            )
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request,
                f'Unexpected error occurred: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        if 'year_label' in form.errors:
            messages.error(self.request, 'Please enter a valid year label format (e.g., 2024-2025).')
        elif 'start_date' in form.errors or 'end_date' in form.errors:
            messages.error(self.request, 'Please check the dates. End date must be after start date.')
        return super().form_invalid(form)


class SemesterListView(LoginRequiredMixin, ListView):
    model = Semester
    template_name = 'student_registration/semester_list.html'
    context_object_name = 'semesters'

class SemesterCreateView(LoginRequiredMixin, CreateView):
    model = Semester
    form_class = SemesterForm
    template_name = 'student_registration/semester_form.html'
    success_url = reverse_lazy('semester_list')
    def form_valid(self, form):
        # Allow Sysadmin or Academic Registrar to create semesters
        if not (self.request.user.is_academic_registrar or self.request.user.is_sysadmin or self.request.user.is_head_of_department):
            messages.error(self.request, "Only Academic Registrar or System Administrator can create semesters.")
            return self.form_invalid(form)
        try:
            self.object = form.save(commit=False)
            if form.cleaned_data.get('is_active'):
                try:
                    Semester.objects.filter(is_active=True).update(is_active=False)
                except DatabaseError:
                    logger.warning("Could not deactivate other semesters, but continuing with save")
            self.object.save()
            messages.success(self.request, 'Semester created successfully!')
            return redirect(self.get_success_url())
        except Exception as e:
            logger.error(f"Error creating semester: {str(e)}")
            messages.error(
                self.request,
                'Error creating semester. Please check your input and try again.'
            )
            return self.form_invalid(form)

class SemesterUpdateView(LoginRequiredMixin, UpdateView):
    model = Semester
    form_class = SemesterForm
    template_name = 'student_registration/semester_form.html'
    success_url = reverse_lazy('semester_list')
    def post(self, request, *args, **kwargs):
        # Allow Sysadmin or Academic Registrar to update semesters
        if not (request.user.is_academic_registrar or request.user.is_sysadmin):
            messages.error(self.request, "Only Academic Registrar or System Administrator can update semesters.")
            return self.form_invalid(self.get_form())
        try:
            return super().post(request, *args, **kwargs)
        except DatabaseError as e:
            logger.error(f"DatabaseError in SemesterUpdateView: {e}")
            messages.error(
                self.request,
                'Database error occurred while updating semester. Please try again.'
            )
            return self.form_invalid(self.get_form())
        except Exception as e:
            logger.error(f"Unexpected error in SemesterUpdateView: {e}")
            messages.error(
                self.request,
                'An unexpected error occurred. Please try again.'
            )
            return self.form_invalid(self.get_form())
    def form_valid(self, form):
        # Allow Sysadmin or Academic Registrar to update semesters
        if not (request.user.is_academic_registrar or request.user.is_sysadmin):
            messages.error(self.request, "Only Academic Registrar or System Administrator can update semesters.")
            return self.form_invalid(form)
        try:
            if form.cleaned_data.get('is_active'):
                try:
                    Semester.objects.filter(is_active=True).exclude(pk=self.object.pk).update(is_active=False)
                except DatabaseError as e:
                    logger.warning(f"Could not deactivate other semesters: {e}")
                    pass
            response = super().form_valid(form)
            messages.success(self.request, 'Semester updated successfully!')
            return response
        except DatabaseError as e:
            logger.error(f"DatabaseError during form validation: {e}")
            messages.error(
                self.request,
                'Database error while saving. Please check your input.'
            )
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Unexpected error during form validation: {e}")
            messages.error(
                self.request,
                'An unexpected error occurred while saving.'
            )
            return self.form_invalid(form)
    def form_invalid(self, form):
        logger.warning(f"Form invalid: {form.errors}")
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class SemesterDeleteView(LoginRequiredMixin, DeleteView):
    model = Semester
    success_url = reverse_lazy('pass_book:semester_list')
    template_name = 'student_registration/semester_confirm_delete.html'
    def delete(self, request, *args, **kwargs):
        # Allow Sysadmin or Academic Registrar to delete semesters
        if not (request.user.is_academic_registrar or request.user.is_sysadmin):
            raise PermissionDenied("Only Academic Registrar or System Administrator can delete semesters.")
        messages.success(request, 'Semester deleted successfully!')
        return super().delete(request, *args, **kwargs)

def semester_set_active(request, pk):
    # Allow Sysadmin or Academic Registrar to set active semester
    if not (request.user.is_academic_registrar or request.user.is_sysadmin):
         raise PermissionDenied("Only Academic Registrar or System Administrator can set the active semester.")
    if request.method == 'POST':
        semester = get_object_or_404(Semester, pk=pk)
        Semester.objects.filter(is_active=True).update(is_active=False)
        semester.is_active = True
        semester.save()
        messages.success(request, f'{semester.get_number_display()} is now the active semester!')
    return redirect('semester_list')

# ============================================================================
# ACCESS NUMBER VIEWS/ SEMESTER CODE FOR END USERS
# ============================================================================

def access_number_list(request):
    access_numbers = AccessNumber.objects.select_related(
        'student', 'academic_year', 'semester'
    ).order_by('-generated_date')
    academic_year_id = request.GET.get('academic_year')
    semester_id = request.GET.get('semester')
    program_code = request.GET.get('program')
    if academic_year_id:
        access_numbers = access_numbers.filter(academic_year_id=academic_year_id)
    if semester_id:
        access_numbers = access_numbers.filter(semester_id=semester_id)
    if program_code:
        access_numbers = access_numbers.filter(student__program__code=program_code)
    context = {
        'access_numbers': access_numbers,
        'academic_years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'selected_academic_year': academic_year_id,
        'selected_semester': semester_id,
        'selected_program': program_code,
    }
    return render(request, 'student_registration/access_number_list.html', context)

def generate_access_number(request, student_id):
    # Allow Sysadmin, Academic Registrar, or HOD to generate access numbers
    if not (request.user.is_academic_registrar or request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only Academic Registrar, Head of Department, or System Administrator can generate access numbers.")
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        form = GenerateAccessNumberForm(request.POST)
        if form.is_valid():
            academic_year = form.cleaned_data['academic_year']
            semester = form.cleaned_data['semester']
            year_of_study = form.cleaned_data['year_of_study']
            if AccessNumber.objects.filter(
                student=student,
                academic_year=academic_year,
                semester=semester
            ).exists():
                messages.warning(request, "Semester code already exists for this semester.")
            else:
                from .models import AccessNumberUtils
                access_number = AccessNumberUtils.create_semester_access_number(
                    student=student,
                    academic_year=academic_year,
                    semester=semester,
                    year_of_study=year_of_study
                )
                messages.success(request, f"Access number {access_number.access_number} created.")
                return redirect('access_number_list')
    else:
        form = GenerateAccessNumberForm()
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'student_registration/access_number_generate_single.html', context)

def bulk_generate_access_numbers(request):
    # Allow Sysadmin, Academic Registrar, or HOD to bulk generate access numbers
    if not (request.user.is_academic_registrar or request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only Academic Registrar, Head of Department, or System Administrator can bulk generate access numbers.")
    
    search_query = request.GET.get('q', '').strip()
    
    if request.method == 'POST':
        form = BulkGenerateAccessNumberForm(request.POST, search_query=search_query)
        if form.is_valid():
            students = form.cleaned_data['students']
            academic_year = form.cleaned_data['academic_year']
            semester = form.cleaned_data['semester']
            year_of_study = form.cleaned_data['year_of_study']
            from .models import AccessNumberUtils
            created = AccessNumberUtils.bulk_generate_access_numbers(
                students=students,
                academic_year=academic_year,
                semester=semester,
                year_of_study=year_of_study
            )
            messages.success(request, f"{len(created)} access numbers generated.")
            return redirect('pass_book:list')
    else:
        form = BulkGenerateAccessNumberForm(search_query=search_query)
    context = {'form': form, 'search_query': search_query}
    return render(request, 'student_registration/access_number_bulk_generate.html', context)

def access_number_detail(request, access_number):
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    semester_registration = getattr(access_num, 'semester_registration', None)
    medical_registration = getattr(access_num, 'medical_registration', None)
    nche_registration = getattr(access_num, 'nche_registration', None)
    internship = getattr(access_num, 'internship', None)
    semester_clearance = getattr(access_num, 'clearance', None)
    course_units = access_num.course_units.select_related('course_unit').all()
    course_works = access_num.course_works.select_related('course_work').all()
    associations = access_num.associations.select_related('association').all()
    context = {
        'access_num': access_num,
        'semester_registration': semester_registration,
        'medical_registration': medical_registration,
        'nche_registration': nche_registration,
        'internship': internship,
        'semester_clearance': semester_clearance,
        'course_units': course_units,
        'course_works': course_works,
        'associations': associations,
    }
    return render(request, 'student_registration/access_number_detail.html', context)

def deactivate_access_number(request, access_number):
    # Allow Sysadmin, Academic Registrar, or HOD to deactivate access numbers
    if not (request.user.is_academic_registrar or request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only Academic Registrar, Head of Department, or System Administrator can deactivate access numbers.")
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    if request.method == 'POST':
        access_num.is_active = False
        access_num.save()
        messages.info(request, f"Access number {access_number} has been deactivated.")
        return redirect('access_number_list')
    context = {'access_num': access_num}
    return render(request, 'student_registration/access_number_confirm_deactivate.html', context)

def edit_access_number_status(request, access_number):
    # Allow Sysadmin, Academic Registrar, or HOD to edit access number status
    if not (request.user.is_academic_registrar or request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only Academic Registrar, Head of Department, or System Administrator can edit access number status.")
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    if request.method == 'POST':
        new_status = request.POST.get('is_active') == 'on'
        access_num.is_active = new_status
        access_num.save()
        status_text = "activated" if new_status else "deactivated"
        messages.success(request, f"Access number {access_number} has been {status_text}.")
        return redirect('pass_book:detail', access_number=access_number)
    context = {
        'access_num': access_num,
    }
    return render(request, 'student_registration/access_number_edit_status.html', context)

# ============================================================================
# SEMESTER REGISTRATION VIEWS
# ============================================================================

@login_required
def semester_registration_view(request, access_number):
    # Allow Sysadmin, Academic Registrar, or HOD to manage semester registration
    if not (request.user.is_academic_registrar or request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only Academic Registrar, Head of Department, or System Administrator can manage semester registration.")
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    try:
        registration = access_num.semester_registration
    except SemesterRegistration.DoesNotExist:
        registration = None
    if request.method == 'POST':
        form = SemesterRegistrationForm(request.POST, request.FILES, instance=registration)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.access_number = access_num
            registration.save()
            messages.success(request, 'Semester registration updated successfully!')
            return redirect('access_number_detail', access_number=access_number)
    else:
        form = SemesterRegistrationForm(instance=registration)
    context = {
        'form': form,
        'access_number': access_num,
        'registration': registration
    }
    return render(request, 'students/semester_registration_form.html', context)

# ============================================================================
# COURSE VIEWS
# ============================================================================
class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'student_registration/course_list.html'
    context_object_name = 'courses'
    paginate_by = 25
    def get_queryset(self):
        queryset = Course.objects.select_related('program').all()
        program_code = self.request.GET.get('program', '').strip()
        search_query = self.request.GET.get('q', '').strip()

        if program_code:
            queryset = queryset.filter(program__code=program_code)

        if search_query:
            queryset = queryset.filter(
                Q(code__icontains=search_query) | Q(name__icontains=search_query)
            )

        return queryset.order_by('code')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['programs'] = Program.objects.all().order_by('code')
        return context

# ============================================================================
# PROGRAM VIEWS
# ============================================================================
class ProgramListView(LoginRequiredMixin, ListView):
    model = Program
    template_name = 'student_registration/program_list.html'
    context_object_name = 'programs'
    paginate_by = 25

    def get_queryset(self):
        queryset = Program.objects.all()
        search_query = self.request.GET.get('q', '').strip()

        if search_query:
            queryset = queryset.filter(
                Q(code__icontains=search_query) | Q(name__icontains=search_query)
            )

        return queryset.order_by('code')

class ProgramCreateView(LoginRequiredMixin, CreateView):
    model = Program
    form_class = ProgramForm
    template_name = 'student_registration/program_form.html'
    success_url = reverse_lazy('pass_book:program_list')

class ProgramUpdateView(LoginRequiredMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = 'student_registration/program_form.html'
    success_url = reverse_lazy('pass_book:program_list')

class ProgramDeleteView(LoginRequiredMixin, DeleteView):
    model = Program
    template_name = 'student_registration/program_confirm_delete.html'
    success_url = reverse_lazy('pass_book:program_list')

# ============================================================================
# COURSE UNIT VIEWS
# ============================================================================

class CourseUnitCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CourseUnit
    form_class = CourseUnitForm
    template_name = 'student_registration/course_unit_form.html'
    success_url = reverse_lazy('pass_book:course_unit_list')
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def form_valid(self, form):
        messages.success(self.request, 'Course unit created successfully!')
        return super().form_valid(form)

class CourseUnitListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CourseUnit
    template_name = 'student_registration/course_unit_list.html'
    context_object_name = 'course_units'
    paginate_by = 20
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def get_queryset(self):
        queryset = CourseUnit.objects.all()
        status = self.request.GET.get('status')
        search_query = self.request.GET.get('q', '').strip()
        
        if search_query:
            queryset = queryset.filter(
                Q(code__icontains=search_query) | 
                Q(title__icontains=search_query) |
                Q(department__icontains=search_query)
            )
        
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        return queryset.order_by('code')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = CourseUnit.objects.count()
        context['active_count'] = CourseUnit.objects.filter(is_active=True).count()
        context['inactive_count'] = CourseUnit.objects.filter(is_active=False).count()
        context['search_query'] = self.request.GET.get('q', '').strip()
        return context

StudentCourseUnitFormSet = inlineformset_factory(
    AccessNumber,
    StudentCourseUnit,
    form=StudentCourseUnitForm,
    extra=5,
    can_delete=True,
)

class StudentCourseUnitManageView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = AccessNumber
    template_name = 'student_registration/student_course_units_manage.html'
    context_object_name = 'access_number'
    slug_field = 'access_number'
    slug_url_kwarg = 'access_number'
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def get_object(self, queryset=None):
        obj = get_object_or_404(
            AccessNumber.objects.select_related('student', 'academic_year', 'semester'),
            access_number=self.kwargs['access_number']
        )
        return obj
    def get_context_data(self, **kwargs):
        access_num = self.get_object()
        ctx = super().get_context_data(**kwargs)
        ctx['course_units'] = access_num.course_units.select_related('course_unit__course').all()
        ctx['available_courses'] = Course.objects.filter(
            course_units__semester_offered=access_num.semester.number
        ).distinct()
        if 'formset' in kwargs:
            ctx['formset'] = kwargs['formset']
        else:
            ctx['formset'] = StudentCourseUnitFormSet(
                instance=access_num,
                form_kwargs={'access_num': access_num}
            )
        ctx['current_semester'] = access_num.semester
        ctx['academic_year'] = access_num.academic_year
        return ctx
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = StudentCourseUnitFormSet(
            request.POST,
            request.FILES,
            instance=self.object,
            form_kwargs={'access_num': self.object}
        )
        if formset.is_valid():
            saved = 0
            for form in formset.forms:
                if form.cleaned_data.get('course_unit') and not form.cleaned_data.get('DELETE'):
                    saved += 1
            formset.save()
            if saved:
                messages.success(request, f'{saved} course unit(s) added successfully!')
            else:
                messages.warning(request, 'No new course units were added.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.error(request, 'Please correct the errors below.')
            return self.render_to_response(self.get_context_data(formset=formset))
    def get_success_url(self):
        return reverse('pass_book:student_course_units_manage', kwargs={
            'access_number': self.object.access_number
        })

@login_required
def student_course_units_view(request, access_number):
    """Manage student's course units - Restricted to HOD and Sysadmin"""
    if not (request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only the Head of Department or System Administrator can manage course units.")
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    if request.method == 'POST':
        formset = StudentCourseUnitFormSet(
            request.POST, request.FILES, instance=access_num
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Course units updated successfully!')
            return redirect('access_number_detail', access_number=access_number)
    else:
        formset = StudentCourseUnitFormSet(instance=access_num)
    context = {
        'formset': formset,
        'access_number': access_num,
        'available_courses': CourseUnit.objects.filter(
            is_active=True,
            semester_offered=access_num.semester.number
        )
    }
    return render(request, 'student_registration/student_course_units_form.html', context)

class StudentCourseUnitBulkCreateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AccessNumber
    fields = []
    template_name = 'student_registration/students_course_units_form2.html'
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def get_object(self, queryset=None):
        return get_object_or_404(AccessNumber, access_number=self.kwargs['access_num_id'])
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        access_num = self.get_object()
        if 'formset' not in kwargs:
            ctx['formset'] = StudentCourseUnitFormSet(
                self.request.POST or None,
                self.request.FILES or None,
                instance=access_num,
                form_kwargs={'access_num': access_num}
            )
        else:
            ctx['formset'] = kwargs['formset']
        ctx['access_number'] = access_num
        ctx['student'] = access_num.student
        return ctx
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            saved = 0
            for form_in_formset in formset.forms:
                if form_in_formset.cleaned_data.get('course_unit') and not form_in_formset.cleaned_data.get('DELETE'):
                    form_in_formset.instance.access_number = self.get_object()
                    saved += 1
            formset.save()
            if saved:
                messages.success(self.request, f'{saved} course unit(s) added successfully!')
            else:
                messages.warning(self.request, 'No course units were added.')
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(formset=formset))
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return self.render_to_response(self.get_context_data())
    def get_success_url(self):
        return reverse_lazy('pass_book:student_course_units', kwargs={
            'access_num_id': self.kwargs['access_num_id']
        })

class StudentCourseUnitListView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = AccessNumber
    template_name = 'student_registration/student_course_units_list.html'
    context_object_name = 'access_number'
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def get_object(self, queryset=None):
        return get_object_or_404(AccessNumber, access_number=self.kwargs['access_num_id'])
    def get_context_data(self, **kwargs):
        access_num = self.get_object()
        ctx = super().get_context_data(**kwargs)
        ctx['course_units'] = access_num.course_units.all().select_related('course_unit')
        if 'formset' in kwargs:
            ctx['formset'] = kwargs['formset']
        else:
            ctx['formset'] = StudentCourseUnitFormSet(
                instance=access_num,
                form_kwargs={'access_num': access_num}
            )
        return ctx
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = StudentCourseUnitFormSet(
            request.POST,
            request.FILES,
            instance=self.object,
            form_kwargs={'access_num': self.object}
        )
        if formset.is_valid():
            saved = 0
            for form in formset.forms:
                if form.cleaned_data.get('course_unit') and not form.cleaned_data.get('DELETE'):
                    saved += 1
            formset.save()
            if saved:
                messages.success(request, f'{saved} course unit(s) added successfully!')
            else:
                messages.warning(request, 'No valid course units were added.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.error(request, 'Please correct the errors below.')
            return self.render_to_response(self.get_context_data(formset=formset))
    def get_success_url(self):
        return reverse_lazy('pass_book:student_course_units', kwargs={
            'access_num_id': self.kwargs['access_num_id']
        })

class StudentCourseUnitUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StudentCourseUnit
    form_class = StudentCourseUnitForm
    template_name = 'student_registration/student_course_unit_form_single.html'
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def form_valid(self, form):
        messages.success(self.request, 'Course unit updated successfully!')
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy('pass_book:student_course_units',
                          kwargs={'access_number': self.object.access_number.access_number})

class StudentCourseUnitCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = StudentCourseUnit
    form_class = StudentCourseUnitForm
    template_name = 'student_registration/students_course_units_form_single.html'
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['access_number'] = get_object_or_404(AccessNumber, pk=self.kwargs['access_num_id'])
        return ctx
    def form_valid(self, form):
        access_num = get_object_or_404(AccessNumber, pk=self.kwargs['access_num_id'])
        course_unit = form.cleaned_data['course_unit']
        if StudentCourseUnit.objects.filter(access_number=access_num, course_unit=course_unit).exists():
            form.add_error(
                'course_unit',
                f"This course unit '{course_unit.code} - {course_unit.title}' is already registered for this access number."
            )
            return self.form_invalid(form)
        form.instance.access_number = access_num
        messages.success(self.request, 'Course unit added successfully!')
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        access_num = get_object_or_404(AccessNumber, pk=self.kwargs['access_num_id'])
        kwargs['access_num'] = access_num
        return kwargs
    def get_success_url(self):
        return reverse_lazy('pass_book:student_course_units',
                          kwargs={'access_num_id': self.kwargs['access_num_id']})

class CourseUnitUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CourseUnit
    form_class = CourseUnitForm
    template_name = 'student_registration/course_unit_form.html'
    success_url = reverse_lazy('pass_book:course_unit_list')
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def form_valid(self, form):
        messages.success(self.request, 'Course unit updated successfully!')
        return super().form_valid(form)

class CourseUnitDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CourseUnit
    template_name = 'student_registration/course_unit_confirm_delete.html'
    success_url = reverse_lazy('pass_book:course_unit_list')
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Course unit "{obj.code} - {obj.title}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

def select_student_for_course_units(request):
    query = request.GET.get('q', '')
    students = []
    if query:
        students = Student.objects.filter(
            Q(name__icontains=query) |
            Q(registration_number__icontains=query)
        ).prefetch_related('access_numbers__semester', 'access_numbers__academic_year')
    context = {
        'query': query,
        'students': students,
    }
    return render(request, 'student_registration/select_student.html', context)

# ============================================================================
# COURSE WORK VIEWS
# ============================================================================

class CourseWorkListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CourseWork
    template_name = 'student_registration/course_work_list.html'
    context_object_name = 'course_works'
    paginate_by = 20
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def get_queryset(self):
        return CourseWork.objects.select_related('course_unit').order_by('-due_date')

class CourseWorkCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CourseWork
    form_class = CourseWorkForm
    template_name = 'student_registration/course_work_form.html'
    success_url = reverse_lazy('pass_book:course_work_list')
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def form_valid(self, form):
        messages.success(self.request, 'Course work created successfully!')
        return super().form_valid(form)

@login_required
def student_course_works_view(request, access_number):
    """Manage student's course work submissions - Restricted to HOD and Sysadmin"""
    if not (request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only the Head of Department or System Administrator can manage course work.")
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    if request.method == 'POST':
        formset = StudentCourseWorkFormSet(
            request.POST, request.FILES, instance=access_num
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Course works updated successfully!')
            return redirect('pass_book:access_number_detail', access_number=access_number)
    else:
        formset = StudentCourseWorkFormSet(instance=access_num)
    student_course_units = access_num.course_units.values_list('course_unit', flat=True)
    available_works = CourseWork.objects.filter(
        course_unit__in=student_course_units
    )
    context = {
        'formset': formset,
        'access_number': access_num,
        'available_works': available_works
    }
    return render(request, 'students/student_course_works_form.html', context)

class CourseWorkUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CourseWork
    form_class = CourseWorkForm
    template_name = 'student_registration/course_work_form.html'
    success_url = reverse_lazy('pass_book:course_work_list')
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def form_valid(self, form):
        messages.success(self.request, 'Course work updated successfully!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class StudentCourseWorkListView(View):
    template_name = 'student_registration/student_course_work_list.html'
    def get(self, request):
        query = request.GET.get('q')
        if query:
            students = Student.objects.filter(
                models.Q(name__icontains=query) |
                models.Q(registration_number__icontains=query)
            ).order_by('name')
        else:
            students = Student.objects.all().order_by('name')
        return render(request, self.template_name, {
            'students': students,
            'query': query
        })

@method_decorator(login_required, name='dispatch')
class AccessNumberCourseWorkListView(View):
    template_name = 'student_registration/student_course_work_access_number_list.html'
    def get(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)
        access_numbers = student.access_numbers.select_related('academic_year', 'semester').all()
        if not access_numbers.exists():
            messages.warning(request, f"No access numbers found for {student.name}.")
            return redirect('pass_book:student_list')
        return render(request, self.template_name, {
            'student': student,
            'access_numbers': access_numbers
        })

@method_decorator(login_required, name='dispatch')
class StudentCourseWorkCreateUpdateView(View):
    template_name = 'student_registration/student_course_work_form2.html'
    def get(self, request, access_number):
        # Check permission
        if not (request.user.is_head_of_department or request.user.is_sysadmin):
            raise PermissionDenied("Only the Head of Department or System Administrator can manage course work certifications.")
        access_num = get_object_or_404(
            AccessNumber.objects.prefetch_related(
                'course_works__course_work__course_unit'
            ),
            access_number=access_number
        )
        course_works = access_num.course_works.all()
        formset = StudentCourseWorkFormSet(
            instance=access_num,
            form_kwargs={'access_num': access_num}
        )
        return render(request, self.template_name, {
            'access_num': access_num,
            'student': access_num.student,
            'course_works': course_works,
            'formset': formset,
        })
    def post(self, request, access_number):
        # Check permission
        if not (request.user.is_head_of_department or request.user.is_sysadmin):
            raise PermissionDenied("Only the Head of Department or System Administrator can manage course work certifications.")
        access_num = get_object_or_404(AccessNumber, access_number=access_number)
        formset = StudentCourseWorkFormSet(
            request.POST,
            request.FILES,
            instance=access_num,
            form_kwargs={'access_num': access_num}
        )
        if formset.is_valid():
            saved = sum(1 for f in formset.forms if f.cleaned_data.get('course_work') and not f.cleaned_data.get('DELETE'))
            formset.save()
            if saved:
                messages.success(request, f'{saved} course work(s) added successfully!')
            else:
                messages.warning(request, 'No new course works were added.')
            return redirect('pass_book:course_work_detail', access_number=access_number)
        else:
            messages.error(request, 'Please correct the errors below.')
            return render(request, self.template_name, {
                'access_num': access_num,
                'student': access_num.student,
                'course_works': access_num.course_works.all(),
                'formset': formset,
            })

@method_decorator(login_required, name='dispatch')
class StudentCourseWorkDetailView(DetailView):
    model = AccessNumber
    template_name = 'student_registration/student_course_work_detail.html'
    context_object_name = 'access_num'
    slug_field = 'access_number'
    slug_url_kwarg = 'access_number'
    def get_queryset(self):
        return AccessNumber.objects.select_related('student', 'academic_year', 'semester')
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course_works'] = self.object.course_works.prefetch_related('course_work__course_unit').all()
        return ctx

@method_decorator(login_required, name='dispatch')
class StudentCourseWorkDeleteView(DeleteView):
    model = StudentCourseWork
    template_name = 'student_registration/student_course_work_delete.html'
    success_url = None
    def get_success_url(self):
        return reverse_lazy('pass_book:course_work_detail', kwargs={
            'access_number': self.object.access_number.access_number
        })
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Course work deleted successfully.")
        return super().delete(request, *args, **kwargs)
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Allow Sysadmin, HOD, or Academic Registrar to delete course work (if HOD-certified, might need specific check)
        if not (request.user.is_head_of_department or request.user.is_sysadmin):
            messages.error(request, "Only the Head of Department or System Administrator can delete course work records.")
            return redirect('pass_book:course_work_detail', access_number=self.object.access_number.access_number)
        if self.object.hod_certified:
            messages.error(request, "Cannot delete a HOD-certified course work record.")
            return redirect('pass_book:course_work_detail', access_number=self.object.access_number.access_number)
        return super().get(request, *args, **kwargs)

def assign_coursework_view(request, course_work_id):
    # Allow HOD or Sysadmin to assign coursework
    if not (request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only the Head of Department or System Administrator can assign coursework.")
    course_work = get_object_or_404(CourseWork, id=course_work_id)
    enrolled_students = AccessNumber.objects.filter(
        course_units__course_unit=course_work.course_unit
    ).distinct()
    assignments = StudentCourseWork.objects.filter(course_work=course_work).select_related('access_number')
    if request.method == "POST":
        form = AssignCourseWorkForm(request.POST, course_work=course_work)
        if form.is_valid():
            student = form.cleaned_data['student']
            status = form.cleaned_data['status']
            submission_date = form.cleaned_data['submission_date']
            existing, created = StudentCourseWork.objects.get_or_create(
                access_number=student,
                course_work=course_work,
                defaults={
                    'status': status,
                    'submission_date': submission_date,
                }
            )
            if not created:
                existing.status = status
                existing.submission_date = submission_date
                existing.save()
                messages.success(request, f"Updated assignment for {student.access_number}")
            messages.success(request, f"Assigned '{course_work.title}' to {student.access_number}")
            return redirect('pass_book:assign_coursework', course_work_id=course_work.id)
    else:
        form = AssignCourseWorkForm(course_work=course_work)
    context = {
        'course_work': course_work,
        'form': form,
        'assignments': assignments,
        'enrolled_students': enrolled_students,
    }
    return render(request, 'student_registration/assign.html', context)

def delete_assignment(request, assignment_id):
    # Allow HOD or Sysadmin to delete assignments
    if not (request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only the Head of Department or System Administrator can delete assignments.")
    assignment = get_object_or_404(StudentCourseWork, id=assignment_id)
    course_work_id = assignment.course_work.id
    if request.method == "POST":
        assignment.delete()
        messages.success(request, f"Assignment deleted for {assignment.access_number.access_number}")
        return redirect('pass_book:assign_coursework', course_work_id=course_work_id)
    return render(request, 'student_registration/delete_confirm.html', {'assignment': assignment})

class CourseWorkDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CourseWork
    template_name = 'student_registration/course_work_confirm_delete.html'
    success_url = reverse_lazy('pass_book:course_work_list')
    def test_func(self):
        # Allow HOD or Sysadmin
        return self.request.user.is_head_of_department or self.request.user.is_sysadmin
    def form_valid(self, form):
        messages.success(self.request, 'Course work deleted successfully!')
        return super().form_valid(form)

# ============================================================================
# ASSOCIATION VIEWS
# ============================================================================

@login_required
def select_student_for_association_view(request):
    query = request.GET.get('q', '').strip()
    selected_access_number = request.GET.get('access_number', None)
    access_numbers = AccessNumber.objects.none()
    if query:
        access_numbers = AccessNumber.objects.filter(
            Q(access_number__icontains=query) |
            Q(student__name__icontains=query) |
            Q(student__registration_number__icontains=query) |
            Q(student__static_access_number__icontains=query) |
            Q(student__student_number__icontains=query)
        ).select_related('student', 'academic_year', 'semester').filter(is_active=True)
    if selected_access_number:
        access_num = get_object_or_404(AccessNumber, access_number=selected_access_number, is_active=True)
        return redirect('pass_book:student_associations', access_number=access_num.access_number)
    context = {
        'query': query,
        'access_numbers': access_numbers,
        'page_title': 'Select Student for Association Management',
    }
    return render(request, 'student_registration/select_student_for_association.html', context)

class AssociationUpdateView(LoginRequiredMixin, UpdateView):
    model = Association
    form_class = AssociationForm
    template_name = 'student_registration/association_form.html'
    success_url = reverse_lazy('pass_book:association_list')

class AssociationDeleteView(LoginRequiredMixin, DeleteView):
    model = Association
    template_name = 'student_registration/association_confirm_delete.html'
    success_url = reverse_lazy('pass_book:association_list')
    def delete(self, request, *args, **kwargs):
        # Allow Sysadmin, Academic Registrar, or Dean of Students to delete associations
        if not (request.user.is_academic_registrar or request.user.is_dean_of_students or request.user.is_sysadmin):
            raise PermissionDenied("Only Academic Registrar, Dean of Students, or System Administrator can delete associations.")
        messages.success(request, f'Association "{self.get_object().name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)

class AssociationListView(LoginRequiredMixin, ListView):
    model = Association
    template_name = 'student_registration/association_list.html'
    context_object_name = 'associations'
    def get_queryset(self):
        return Association.objects.filter(is_active=True).order_by('name')

class AssociationCreateView(LoginRequiredMixin, CreateView):
    model = Association
    form_class = AssociationForm
    template_name = 'student_registration/association_form.html'
    success_url = reverse_lazy('pass_book:association_list')
    def form_valid(self, form):
        messages.success(self.request, 'Association created successfully!')
        return super().form_valid(form)

class AccessAssociationNumberDetailView(LoginRequiredMixin, DetailView):
    model = AccessNumber
    template_name = 'student_registration/association_access_number_detail.html'
    context_object_name = 'access_number'
    slug_field = 'access_number'
    slug_url_kwarg = 'access_number'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['memberships'] = self.object.student_associations.select_related('association').all()
        return context

@login_required
def student_associations_view(request, access_number):
    """Manage student's association memberships - Restricted to Dean of Students and Sysadmin."""
    if not (request.user.is_dean_of_students or request.user.is_sysadmin):
        raise PermissionDenied("Only the Dean of Students or System Administrator can manage association memberships.")
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    if request.method == 'POST':
        formset = StudentAssociationFormSet(
            request.POST,
            request.FILES,
            instance=access_num
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Associations updated successfully!')
            return redirect('pass_book:detail', access_number=access_number)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        formset = StudentAssociationFormSet(instance=access_num)
    context = {
        'formset': formset,
        'access_number': access_num,
        'available_associations': Association.objects.filter(is_active=True)
    }
    return render(request, 'student_registration/student_associations_form.html', context)

# ============================================================================
# DEAD SEMESTER APPLICATION VIEWS
# ============================================================================

class DeadSemesterApplicationListView(LoginRequiredMixin, ListView):
    model = DeadSemesterApplication
    template_name = 'student_registration/dead_semester_list.html'
    context_object_name = 'applications'
    paginate_by = 20
    def get_queryset(self):
        return DeadSemesterApplication.objects.select_related('student').order_by('-application_date')

@login_required
def select_student_for_dead_semester_view(request):
    query = request.GET.get('q', '').strip()
    students = Student.objects.none()
    if query:
        students = Student.objects.filter(
            Q(name__icontains=query) |
            Q(static_access_number__icontains=query) |
            Q(registration_number__icontains=query)
        ).distinct()
    context = {
        'students': students,
        'query': query,
    }
    return render(request, 'student_registration/select_student_for_dead_semester.html', context)

@login_required
def dead_semester_application_create_view(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    if request.method == 'POST':
        form = DeadSemesterApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.student = student
            application.save()
            messages.success(request, 'Dead semester application submitted successfully!')
            return redirect('pass_book:student_detail', pk=student.pk)
    else:
        form = DeadSemesterApplicationForm()
    context = {
        'form': form,
        'student': student
    }
    return render(request, 'student_registration/dead_semester_form.html', context)

class DeadSemesterApplicationDetailView(LoginRequiredMixin, DetailView):
    model = DeadSemesterApplication
    template_name = 'student_registration/dead_semester_detail.html'
    context_object_name = 'application'
    pk_url_kwarg = 'pk'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dead_app = self.object
        context['has_resumption'] = hasattr(dead_app, 'resumption')
        context['student'] = dead_app.student
        context['approval_status'] = dead_app.approval_status
        return context
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except:
            messages.error(request, "Invalid or missing application.")
            return redirect('pass_book:dead_semester_list')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

@login_required
def hod_recommend_view(request, pk):
    """HOD recommendation for dead semester - Restricted to HOD and Sysadmin"""
    if not (request.user.is_head_of_department or request.user.is_sysadmin):
        raise PermissionDenied("Only the Head of Department or System Administrator can provide recommendations.")
    application = get_object_or_404(DeadSemesterApplication, pk=pk)
    if request.method == 'POST':
        form = DeadSemesterApplicationForm(request.POST, request.FILES, instance=application, mode='hod')
        if form.is_valid():
            form.save()
            messages.success(request, "HOD recommendation saved successfully!")
            return redirect('pass_book:dead_semester_detail', pk=pk)
    else:
        form = DeadSemesterApplicationForm(instance=application, mode='hod')
    if (application.hod_recommended and
            application.faculty_recommended and
            application.registrar_recommended):
        application.approved = True
        application.verified = True
        application.save()
        messages.success(request, "✅ All approvals received! Application is now APPROVED.")
    else:
        messages.success(request, "HOD recommendation saved successfully!")
    return render(request, 'student_registration/hod_recommend_form.html', {
        'form': form,
        'application': application,
    })

@login_required
def faculty_recommend_view(request, pk):
    """Faculty recommendation for dead semester - Restricted to Faculty Dean and Sysadmin"""
    if not (request.user.is_faculty_dean or request.user.is_sysadmin):
        raise PermissionDenied("Only the Faculty Dean or System Administrator can provide recommendations.")
    application = get_object_or_404(DeadSemesterApplication, pk=pk)
    if request.method == 'POST':
        faculty_recommended = request.POST.get('faculty_recommended') == 'on'
        faculty_name = request.POST.get('faculty_name', '').strip()
        faculty_designation = request.POST.get('faculty_designation', '').strip()
        faculty_department = request.POST.get('faculty_department', '').strip()
        faculty_date = request.POST.get('faculty_date')
        errors = []
        if not faculty_name:
            errors.append("Faculty name is required.")
        if not faculty_designation:
            errors.append("Designation is required.")
        if not faculty_department:
            errors.append("Department is required.")
        if not faculty_date:
            errors.append("Recommendation date is required.")
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'student_registration/faculty_recommend_form.html', {
                'application': application,
                'posted_data': request.POST,
            })
        faculty_signature = request.FILES.get('faculty_signature')
        signature_path = None
        if faculty_signature:
            folder = 'faculty_dead_semester_signatures/'
            filename = f"{application.pk}_{faculty_signature.name}"
            full_path = os.path.join(folder, filename)
            file_path = default_storage.save(full_path, ContentFile(faculty_signature.read()))
            signature_path = file_path
        application.faculty_recommended = faculty_recommended or bool(faculty_name)
        application.faculty_name = faculty_name
        application.faculty_designation = faculty_designation
        application.faculty_department = faculty_department
        application.faculty_date = faculty_date
        if signature_path:
            application.faculty_signature = signature_path
        application.save()
        messages.success(request, "Faculty recommendation saved successfully!")
        return redirect('pass_book:dead_semester_detail', pk=pk)
    if (application.hod_recommended and
        application.faculty_recommended and
        application.registrar_recommended):
        application.approved = True
        application.verified = True
        application.save()
        messages.success(request, "✅ All approvals received! Application is now APPROVED.")
    else:
        messages.success(request, "Faculty recommendation saved successfully!")
    return render(request, 'student_registration/faculty_recommend_form.html', {
        'application': application,
    })

@login_required
def registrar_recommend_view(request, pk):
    """Registrar recommendation for dead semester - Restricted to Academic Registrar and Sysadmin"""
    if not (request.user.is_academic_registrar or request.user.is_sysadmin):
        raise PermissionDenied("Only the Academic Registrar or System Administrator can provide recommendations.")
    application = get_object_or_404(DeadSemesterApplication, pk=pk)
    if request.method == 'POST':
        registrar_recommended = request.POST.get('registrar_recommended') == 'on'
        registrar_name = request.POST.get('registrar_name', '').strip()
        registrar_designation = request.POST.get('registrar_designation', '').strip()
        registrar_department = request.POST.get('registrar_department', '').strip()
        registrar_date = request.POST.get('registrar_date')
        errors = []
        if not registrar_name:
            errors.append("Registrar name is required.")
        if not registrar_designation:
            errors.append("Designation is required.")
        if not registrar_department:
            errors.append("Department is required.")
        if not registrar_date:
            errors.append("Recommendation date is required.")
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'student_registration/registrar_recommend_form.html', {
                'application': application,
                'posted_data': request.POST,
            })
        registrar_signature = request.FILES.get('registrar_signature')
        signature_path = None
        if registrar_signature:
            folder = 'registrar_dead_semester_signatures/'
            filename = f"{application.pk}_{registrar_signature.name}"
            full_path = os.path.join(folder, filename)
            file_path = default_storage.save(full_path, ContentFile(registrar_signature.read()))
            signature_path = file_path
        application.registrar_recommended = registrar_recommended or bool(registrar_name)
        application.registrar_name = registrar_name
        application.registrar_designation = registrar_designation
        application.registrar_department = registrar_department
        application.registrar_date = registrar_date
        if signature_path:
            application.registrar_signature = signature_path
        application.save()
        messages.success(request, "Registrar recommendation saved successfully!")
        return redirect('pass_book:dead_semester_detail', pk=pk)
    if (application.hod_recommended and
        application.faculty_recommended and
        application.registrar_recommended):
        application.approved = True
        application.verified = True
        application.save()
        messages.success(request, "✅ All approvals received! Application is now APPROVED.")
    else:
        messages.success(request, "Registrar recommendation saved successfully!")
    return render(request, 'student_registration/registrar_recommend_form.html', {
        'application': application,
    })

@login_required
def resumption_application_create_view(request, dead_app_pk):
    dead_app = get_object_or_404(DeadSemesterApplication, pk=dead_app_pk)
    if hasattr(dead_app, 'resumption'):
        messages.warning(request, 'Resumption application already exists!')
        return redirect('pass_book:dead_semester_detail', pk=dead_app.pk)
    if request.method == 'POST':
        form = ResumptionApplicationForm(request.POST)
        if form.is_valid():
            resumption = form.save(commit=False)
            resumption.dead_semester_application = dead_app
            resumption.save()
            messages.success(request, 'Resumption application submitted successfully!')
            return redirect('pass_book:dead_semester_detail', pk=dead_app.pk)
    else:
        form = ResumptionApplicationForm()
    context = {
        'form': form,
        'dead_application': dead_app
    }
    return render(request, 'student_registration/resumption_form.html', context)

# ============================================================================
# BBALA LAPTOP SCHEME VIEWS
# ============================================================================

class BbalaLaptopSchemeListView(LoginRequiredMixin, ListView):
    model = BbalaLaptopScheme
    template_name = 'student_registration/laptop_scheme_list.html'
    context_object_name = 'schemes'
    paginate_by = 20
    def get_queryset(self):
        return BbalaLaptopScheme.objects.select_related('student').order_by('student__name')

@login_required
def select_student_for_laptop_scheme_view(request):
    query = request.GET.get('q', '').strip()
    selected_student_id = request.GET.get('student_id', None)
    students = Student.objects.none()
    if query:
        students = Student.objects.filter(
            Q(name__icontains=query) |
            Q(student_number__icontains=query) |
            Q(static_access_number__icontains=query) |
            Q(registration_number__icontains=query)
        ).select_related('program').order_by('name')
    if selected_student_id:
        student = get_object_or_404(Student, pk=selected_student_id)
        return redirect('pass_book:laptop_scheme_create', student_pk=student.pk)
    context = {
        'query': query,
        'students': students,
        'page_title': 'Select Student for Laptop Scheme',
    }
    return render(request, 'student_registration/select_student_for_laptop_scheme.html', context)

@login_required
def laptop_scheme_create_view(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    if hasattr(student, 'laptop_scheme'):
        messages.warning(request, 'Student is already enrolled in the laptop scheme!')
        return redirect('pass_book:student_detail', pk=student.pk)
    if request.method == 'POST':
        form = BbalaLaptopSchemeForm(request.POST)
        if form.is_valid():
            scheme = form.save(commit=False)
            scheme.student = student
            scheme.save()
            messages.success(request, 'Student enrolled in laptop scheme successfully!')
            return redirect('pass_book:student_detail', pk=student.pk)
    else:
        form = BbalaLaptopSchemeForm()
    context = {
        'form': form,
        'student': student
    }
    return render(request, 'student_registration/laptop_scheme_form.html', context)

@login_required
def laptop_scheme_update_view(request, pk):
    """Update laptop scheme details - Restricted to Finance Director and Sysadmin."""
    if not (request.user.is_finance_director or request.user.is_sysadmin):
        raise PermissionDenied("Only the Finance Director or System Administrator can update laptop scheme payments.")
    scheme = get_object_or_404(BbalaLaptopScheme, pk=pk)
    student = scheme.student
    if request.method == 'POST':
        form = BbalaLaptopSchemeForm(request.POST, instance=scheme)
        if form.is_valid():
            form.save()
            messages.success(request, 'Laptop scheme updated successfully!')
            return redirect('pass_book:student_detail', pk=student.pk)
    else:
        form = BbalaLaptopSchemeForm(instance=scheme)
    context = {
        'form': form,
        'scheme': scheme,
        'student': student,
    }
    return render(request, 'student_registration/laptop_scheme_form.html', context)

# ============================================================================
# MEDICAL AND NCHE REGISTRATION VIEWS
# ============================================================================

@login_required
def medical_registration_view(request, access_number):
    """Medical registration for a student - Restricted to Medical Officer and Sysadmin."""
    if not (request.user.is_medical_officer or request.user.is_sysadmin):
        raise PermissionDenied("Only a Medical Officer or System Administrator can register students for medical services.")
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    try:
        registration = access_num.medical_registration
    except MedicalRegistration.DoesNotExist:
        registration = None
    if request.method == 'POST':
        form = MedicalRegistrationForm(request.POST, request.FILES, instance=registration)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.access_number = access_num
            registration.save()
            messages.success(request, 'Medical registration completed successfully!')
            return redirect('access_number_detail', access_number=access_number)
    else:
        form = MedicalRegistrationForm(instance=registration)
    context = {
        'form': form,
        'access_number': access_num,
        'registration': registration
    }
    return render(request, 'student_registration/medical_registration_form.html', context)

@login_required
def medical_registration_list(request):
    registrations = MedicalRegistration.objects.select_related('access_number').order_by('-registration_date')
    search_query = request.GET.get('search')
    if search_query:
        registrations = registrations.filter(
            Q(access_number__access_number__icontains=search_query) |
            Q(medical_officer_name__icontains=search_query)
        )
    paginator = Paginator(registrations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_count': registrations.count()
    }
    return render(request, 'student_registration/medical_registration_list.html', context)

@login_required
def medical_registration_create(request, access_number):
    # Allow Medical Officer or Sysadmin
    if not (request.user.is_medical_officer or request.user.is_sysadmin):
        raise PermissionDenied("Only a Medical Officer or System Administrator can register students for medical services.")
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    if hasattr(access_num, 'medical_registration'):
        messages.warning(request, 'Medical registration already exists for this student.')
        return redirect('pass_book:medical_registration_detail', access_number=access_number)
    if request.method == 'POST':
        form = MedicalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.access_number = access_num
            registration.save()
            messages.success(request, 'Medical registration created successfully!')
            return redirect('pass_book:medical_registration_list')
    else:
        form = MedicalRegistrationForm()
    context = {
        'form': form,
        'access_number': access_num,
        'page_title': 'Create Medical Registration'
    }
    return render(request, 'student_registration/medical_registration_form.html', context)

@login_required
def medical_registration_detail(request, access_number):
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    registration = get_object_or_404(MedicalRegistration, access_number=access_num)
    context = {
        'registration': registration,
        'access_number': access_num
    }
    return render(request, 'student_registration/medical_registration_detail.html', context)

@login_required
def select_student_for_medical(request):
    # Allow Medical Officer or Sysadmin
    if not (request.user.is_medical_officer or request.user.is_sysadmin):
        raise PermissionDenied("Only a Medical Officer or System Administrator can register students for medical services.")
    students = AccessNumber.objects.select_related('student').order_by('access_number')
    students_without_medical = students.filter(medical_registration__isnull=True)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        students_without_medical = students_without_medical.filter(
            Q(access_number__icontains=search_query) |
            Q(student__name__icontains=search_query) |
            Q(student__registration_number__icontains=search_query) |
            Q(student__static_access_number__icontains=search_query) |
            Q(student__program__code__icontains=search_query) |
            Q(student__admission_year__icontains=search_query) |
            Q(student__session__icontains=search_query)
        )
    paginator = Paginator(students_without_medical, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_count': students_without_medical.count()
    }
    return render(request, 'student_registration/select_student_medical.html', context)

@login_required
def nche_registration_view(request, access_number):
    """NCHE registration for a student - Restricted to NCHE Officer and Sysadmin."""
    if not (request.user.is_nche_officer or request.user.is_sysadmin):
        raise PermissionDenied("Only an NCHE Officer or System Administrator can register students for NCHE.")
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    try:
        registration = access_num.nche_registration
    except NCHERegistration.DoesNotExist:
        registration = None
    if request.method == 'POST':
        form = NCHERegistrationForm(request.POST, request.FILES, instance=registration)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.access_number = access_num
            registration.save()
            messages.success(request, 'NCHE registration completed successfully!')
            return redirect('pass_book:detail', access_number=access_number)
    else:
        form = NCHERegistrationForm(instance=registration)
    context = {
        'form': form,
        'access_number': access_num,
        'registration': registration
    }
    return render(request, 'student_registration/nche_registration_form.html', context)

class NCHERegistrationListView(ListView):
    model = NCHERegistration
    template_name = 'student_registration/nche_registration_list.html'
    context_object_name = 'registrations'
    paginate_by = 20
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'access_number__student',
            'access_number__academic_year',
            'access_number__semester'
        )
        access_number = self.request.GET.get('access_number')
        if access_number:
            queryset = queryset.filter(
                access_number__access_number__icontains=access_number
            )
        officer_name = self.request.GET.get('officer_name')
        if officer_name:
            queryset = queryset.filter(officer_name__icontains=officer_name)
        registration_date = self.request.GET.get('registration_date')
        if registration_date:
            queryset = queryset.filter(registration_date=registration_date)
        return queryset.order_by('-registration_date')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_registrations'] = self.get_queryset().count()
        return context

class NCHERegistrationDeleteView(DeleteView):
    model = NCHERegistration
    template_name = 'student_registration/nche_registration_delete_confirm.html'
    context_object_name = 'registration'
    def get_object(self):
        access_number = self.kwargs['access_number']
        access_num = get_object_or_404(AccessNumber, access_number=access_number)
        return get_object_or_404(NCHERegistration, access_number=access_num)
    def get_success_url(self):
        messages.success(self.request, 'NCHE registration deleted successfully!')
        return reverse_lazy('pass_book:detail',
                          kwargs={'access_number': self.object.access_number.access_number})
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['access_number'] = self.object.access_number
        return context
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Allow NCHE Officer or Sysadmin
        if not (request.user.is_nche_officer or request.user.is_sysadmin):
            raise PermissionDenied("Only an NCHE Officer or System Administrator can delete NCHE registrations.")
        student_name = self.object.access_number.student.name
        access_number = self.object.access_number.access_number
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'NCHE registration for {student_name} ({access_number}) has been deleted successfully!'
        )
        return response

@login_required
def student_selection_view(request):
    # Allow NCHE Officer or Sysadmin
    if not (request.user.is_nche_officer or request.user.is_sysadmin):
        raise PermissionDenied("Only an NCHE Officer or System Administrator can manage NCHE registrations.")
    queryset = AccessNumber.objects.select_related(
        'student',
        'academic_year',
        'semester'
    ).prefetch_related(
        Prefetch(
            'nche_registration',
            queryset=NCHERegistration.objects.select_related('access_number')
        )
    ).filter(is_active=True)
    student_name = request.GET.get('student_name', '').strip()
    access_number_filter = request.GET.get('access_number', '').strip()
    academic_year_id = request.GET.get('academic_year', '').strip()
    if student_name:
        queryset = queryset.filter(
            Q(student__name__icontains=student_name) |
            Q(student__student_id__icontains=student_name)
        )
    if access_number_filter:
        queryset = queryset.filter(
            access_number__icontains=access_number_filter
        )
    if academic_year_id:
        queryset = queryset.filter(academic_year_id=academic_year_id)
    queryset = queryset.annotate(
        has_nche_registration=Exists(
            NCHERegistration.objects.filter(access_number=OuterRef('pk'))
        )
    )
    queryset = queryset.order_by('has_nche_registration', '-generated_date')
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    academic_years = AcademicYear.objects.filter(is_active=True).order_by('-year_label')
    context = {
        'access_numbers': page_obj,
        'academic_years': academic_years,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_students': queryset.count(),
    }
    return render(request, 'student_registration/nche_registration_select_student.html', context)

# ============================================================================
# INTERNSHIP VIEWS
# ============================================================================

@login_required
def internship_dashboard(request):
    recent_internships = Internship.objects.select_related(
        'access_number__student'
    ).order_by('-access_number__generated_date')[:10]
    stats = {
        'total_internships': Internship.objects.count(),
        'done_internships': Internship.objects.filter(status='DONE').count(),
        'not_done_internships': Internship.objects.filter(status='NOT_DONE').count(),
        'total_students': AccessNumber.objects.filter(is_active=True).count(),
    }
    context = {
        'recent_internships': recent_internships,
        'stats': stats,
    }
    return render(request, 'student_registration/internship_dashboard.html', context)

@login_required
def student_search(request):
    form = StudentSearchForm(request.GET or None)
    students = AccessNumber.objects.select_related('student').filter(is_active=True)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        academic_year = form.cleaned_data.get('academic_year')
        semester = form.cleaned_data.get('semester')
        year_of_study = form.cleaned_data.get('year_of_study')
        status = form.cleaned_data.get('status')
        if query:
            students = students.filter(
                Q(access_number__icontains=query) |
                Q(student__name__icontains=query) |
                Q(student__email__icontains=query)
            )
        if academic_year:
            students = students.filter(academic_year=academic_year)
        if semester:
            students = students.filter(semester=semester)
        if year_of_study:
            students = students.filter(year_of_study=year_of_study)
        if status:
            if status == 'HAS_INTERNSHIP':
                students = students.filter(internship__isnull=False)
            elif status == 'NO_INTERNSHIP':
                students = students.filter(internship__isnull=True)
            elif status in ['DONE', 'NOT_DONE']:
                students = students.filter(internship__status=status)
    students = students.order_by('-generated_date')
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'form': form,
        'page_obj': page_obj,
        'students': page_obj,
    }
    return render(request, 'student_registration/internship_search.html', context)

@login_required
def internship_view(request, access_number):
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    try:
        internship = access_num.internship
    except Internship.DoesNotExist:
        internship = None
    if request.method == 'POST':
        form = InternshipForm(request.POST, instance=internship)
        if form.is_valid():
            internship = form.save(commit=False)
            internship.access_number = access_num
            internship.save()
            messages.success(request, 'Internship details updated successfully!')
            return redirect('pass_book:internship_detail', access_number=access_number)
    else:
        form = InternshipForm(instance=internship)
    context = {
        'form': form,
        'access_number': access_num,
        'internship': internship,
        'student': access_num.student,
    }
    return render(request, 'student_registration/internship_form.html', context)

@login_required
def internship_detail(request, access_number):
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    try:
        internship = access_num.internship
    except Internship.DoesNotExist:
        internship = None
    context = {
        'access_number': access_num,
        'internship': internship,
        'student': access_num.student,
    }
    return render(request, 'student_registration/internship_detail.html', context)

@login_required
def internship_list(request):
    internships = Internship.objects.select_related(
        'access_number__student',
        'access_number__academic_year',
        'access_number__semester'
    ).all()
    status_filter = request.GET.get('status')
    if status_filter:
        internships = internships.filter(status=status_filter)
    year_filter = request.GET.get('year')
    if year_filter:
        internships = internships.filter(access_number__academic_year__id=year_filter)
    search_query = request.GET.get('search')
    if search_query:
        internships = internships.filter(
            Q(access_number__access_number__icontains=search_query) |
            Q(access_number__student__name__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(supervisor_name__icontains=search_query)
        )
    internships = internships.order_by('-access_number__generated_date')
    paginator = Paginator(internships, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'internships': page_obj,
        'status_choices': Internship.STATUS_CHOICES,
    }
    return render(request, 'student_registration/internship_list.html', context)

@login_required
def internship_delete(request, access_number):
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    try:
        internship = access_num.internship
    except Internship.DoesNotExist:
        messages.error(request, 'No internship record found for this student.')
        return redirect('pass_book:student_search')
    if request.method == 'POST':
        # Allow Academic Registrar, HOD, or Sysadmin to delete internships
        if not (request.user.is_academic_registrar or request.user.is_head_of_department or request.user.is_sysadmin):
            raise PermissionDenied("Only Academic Registrar, Head of Department, or System Administrator can delete internship records.")
        internship.delete()
        messages.success(request, 'Internship record deleted successfully!')
        return redirect('pass_book:student_search')
    context = {
        'internship': internship,
        'access_number': access_num,
        'student': access_num.student,
    }
    return render(request, 'student_registration/internship_delete.html', context)

@login_required
def student_ajax_search(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    students = AccessNumber.objects.select_related('student').filter(
        Q(access_number__icontains=query) |
        Q(student__name__icontains=query) |
        Q(student__email__icontains=query),
        is_active=True
    )[:10]
    results = []
    for student in students:
        has_internship = hasattr(student, 'internship')
        internship_status = student.internship.status if has_internship else None
        results.append({
            'id': student.access_number,
            'text': f"{student.access_number} - {student.student.name}",
            'name': student.student.name,
            'email': student.student.email,
            'has_internship': has_internship,
            'internship_status': internship_status,
        })
    return JsonResponse({'results': results})

# ============================================================================
# CLEARANCE VIEWS
# ============================================================================
@login_required
def semester_clearance_view(request, access_number):
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    try:
        clearance = access_num.clearance
    except SemesterClearance.DoesNotExist:
        clearance = None
    if request.method == 'POST':
        form = SemesterClearanceForm(request.POST, request.FILES, instance=clearance)
        if form.is_valid():
            clearance = form.save(commit=False)
            clearance.access_number = access_num
            clearance.save()
            messages.success(request, 'Semester clearance updated successfully!')
            return redirect('access_number_detail', access_number=access_number)
    else:
        form = SemesterClearanceForm(instance=clearance)
    context = {
        'form': form,
        'access_number': access_num,
        'clearance': clearance
    }
    return render(request, 'students/semester_clearance_form.html', context)


@login_required
def finance_clearance_view(request, access_number):
    """Finance clearance for a student - Restricted to Finance Director and Sysadmin."""
    if not (request.user.is_finance_director or request.user.is_sysadmin):
        raise PermissionDenied("Only the Finance Director or System Administrator can perform financial clearance.")
    
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    
    try:
        clearance = access_num.clearance
    except SemesterClearance.DoesNotExist:
        clearance = SemesterClearance(access_number=access_num)
    
    if request.method == 'POST':
        form = FinanceClearanceForm(request.POST, request.FILES, instance=clearance)
        if form.is_valid():
            clearance = form.save(commit=False)
            if not hasattr(clearance, 'access_number'):
                clearance.access_number = access_num
            clearance.save()
            messages.success(request, 'Finance clearance updated successfully!')
            # Just refresh the same page after successful save
            return redirect('pass_book:finance_clearance', access_number=access_number)
    else:
        form = FinanceClearanceForm(instance=clearance)
    
    context = {
        'form': form,
        'access_number': access_num,
        'student_name': access_num.student.name,
        'next_step_url': 'academic_clearance',  # Kept for template if needed
    }
    return render(request, 'student_registration/sem_clearance_finance.html', context)



@login_required
def academic_clearance_view(request, access_number):
    """Academic clearance for a student - Restricted to Academic Registrar and Sysadmin."""
    if not (request.user.is_academic_registrar or request.user.is_sysadmin):
        raise PermissionDenied("Only the Academic Registrar or System Administrator can perform academic clearance.")
    
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    
    try:
        clearance = access_num.clearance
    except SemesterClearance.DoesNotExist:
        clearance = SemesterClearance(access_number=access_num)
    
    if request.method == 'POST':
        form = AcademicClearanceForm(request.POST, request.FILES, instance=clearance)
        if form.is_valid():
            clearance = form.save(commit=False)
            if not hasattr(clearance, 'access_number'):
                clearance.access_number = access_num
            clearance.save()
            messages.success(request, 'Academic clearance updated successfully!')
            return redirect('pass_book:clearance_detail', access_number=access_number)
    else:
        form = AcademicClearanceForm(instance=clearance)
    
    context = {
        'form': form,
        'access_number': access_num,
        'student_name': access_num.student.name,
        'back_url': 'pass_book:finance_clearance',
    }
    return render(request, 'student_registration/sem_clearance_academic.html', context)

@login_required
def clearance_detail_view(request, access_number):
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    clearance = get_object_or_404(SemesterClearance, access_number=access_num)
    context = {
        'clearance': clearance,
        'access_number': access_num,
        'student': access_num.student,
    }
    return render(request, 'student_registration/sem_clearance_detail.html', context)

@login_required
def delete_clearance_view(request, access_number):
    access_num = get_object_or_404(AccessNumber, access_number=access_number)
    clearance = get_object_or_404(SemesterClearance, access_number=access_num)
    if request.method == 'POST':
        # Allow Finance Director, Academic Registrar, or Sysadmin to delete clearances
        if not (request.user.is_finance_director or request.user.is_academic_registrar or request.user.is_sysadmin):
            raise PermissionDenied("Only Finance Director, Academic Registrar, or System Administrator can delete clearance records.")
        clearance.delete()
        messages.success(request, 'Clearance record deleted.')
        return redirect('pass_book:select_student_for_clearance')
    context = {
        'clearance': clearance,
        'access_number': access_num,
    }
    return render(request, 'student_registration/sem_clearance_delete.html', context)

@login_required
def clearance_list_view(request):
    semester_id = request.GET.get('semester')
    year_id = request.GET.get('academic_year')
    search_query = request.GET.get('search', '').strip()
    access_numbers = AccessNumber.objects.filter(is_active=True).select_related(
        'student', 'academic_year', 'semester', 'clearance'
    ).order_by('-generated_date')
    if semester_id:
        access_numbers = access_numbers.filter(semester_id=semester_id)
    if year_id:
        access_numbers = access_numbers.filter(academic_year_id=year_id)
    if search_query:
        access_numbers = access_numbers.filter(
            Q(access_number__icontains=search_query) |
            Q(student__name__icontains=search_query)
        )
    access_numbers = access_numbers.prefetch_related('clearance')
    paginator = Paginator(access_numbers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    semesters = Semester.objects.all()
    academic_years = AcademicYear.objects.all()
    context = {
        'page_obj': page_obj,
        'semesters': semesters,
        'academic_years': academic_years,
        'selected_semester': semester_id,
        'selected_year': year_id,
        'search_query': search_query,
    }
    return render(request, 'student_registration/sem_clearance_list.html', context)


@login_required
def select_student_for_clearance(request):
    if request.method == 'POST':
        search_input = request.POST.get('access_number', '').strip()
        if not search_input:
            messages.error(request, 'Please enter an Access Number or Registration Number.')
            return render(request, 'student_registration/sem_clearance_select_student.html')
        
        try:
            # Try to find student by static_access_number or registration_number
            student = Student.objects.get(
                models.Q(static_access_number=search_input) | 
                models.Q(registration_number=search_input)
            )
            
            # Get the most recent active access number for this student
            access_number = AccessNumber.objects.filter(
                student=student,
                is_active=True
            ).order_by('-generated_date').first()
            
            if not access_number:
                messages.error(request, 'No active access number found for this student.')
                return render(request, 'student_registration/sem_clearance_select_student.html')
            
            # Check user permissions and redirect with access_number
            if request.user.is_finance_director or request.user.is_sysadmin:
                return redirect('pass_book:finance_clearance', access_number=access_number.access_number)
            elif request.user.is_academic_registrar or request.user.is_sysadmin:
                return redirect('pass_book:academic_clearance', access_number=access_number.access_number)
            else:
                messages.error(request, 'You do not have permission to perform clearance.')
                return render(request, 'student_registration/sem_clearance_select_student.html')
                
        except Student.DoesNotExist:
            messages.error(request, 'Student not found. Please check the number and try again.')
            return render(request, 'student_registration/sem_clearance_select_student.html')
        except Student.MultipleObjectsReturned:
            messages.error(request, 'Multiple students found. Please contact system administrator.')
            return render(request, 'student_registration/sem_clearance_select_student.html')
    
    # Handle GET request - render the selection form
    return render(request, 'student_registration/sem_clearance_select_student.html')
# ============================================================================
# GRADUATION CLEARANCE VIEWS
# ============================================================================

@login_required
def graduation_clearance_view(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    try:
        clearance = student.graduation_clearance
    except GraduationClearance.DoesNotExist:
        clearance = None
    if request.method == 'POST':
        form = GraduationClearanceForm(request.POST, request.FILES, instance=clearance)
        if form.is_valid():
            clearance = form.save(commit=False)
            clearance.student = student
            clearance.save()
            messages.success(request, 'Graduation clearance updated successfully!')
            return redirect('student_detail', pk=student.pk)
    else:
        form = GraduationClearanceForm(instance=clearance)
    context = {
        'form': form,
        'student': student,
        'clearance': clearance
    }
    return render(request, 'students/graduation_clearance_form.html', context)

@login_required
def graduation_clearance_list(request):
    clearances = GraduationClearance.objects.select_related('student', 'student__program')
    search_query = request.GET.get('search', '')
    if search_query:
        clearances = clearances.filter(
            Q(student__name__icontains=search_query) |
            Q(student__registration_number__icontains=search_query) |
            Q(student__static_access_number__icontains=search_query) |
            Q(approving_officer_name__icontains=search_query)
        )
    status_filter = request.GET.get('status', '')
    if status_filter == 'cleared':
        clearances = clearances.filter(all_requirements_met=True)
    elif status_filter == 'pending':
        clearances = clearances.filter(all_requirements_met=False)
    program_filter = request.GET.get('program', '')
    if program_filter:
        clearances = clearances.filter(student__program__id=program_filter)
    year_filter = request.GET.get('year', '')
    if year_filter:
        clearances = clearances.filter(student__admission_year=year_filter)
    paginator = Paginator(clearances, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    from .models import Program
    programs = Program.objects.all()
    years = Student.objects.values_list('admission_year', flat=True).distinct().order_by('-admission_year')
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'program_filter': program_filter,
        'year_filter': year_filter,
        'programs': programs,
        'years': years,
        'total_count': clearances.count()
    }
    return render(request, 'student_registration/grad_clearance_list.html', context)

@login_required
def student_selection_view(request):
    students = Student.objects.select_related('program').prefetch_related('graduation_clearance')
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) |
            Q(registration_number__icontains=search_query) |
            Q(static_access_number__icontains=search_query)
        )
    program_filter = request.GET.get('program', '')
    if program_filter:
        students = students.filter(program__id=program_filter)
    year_filter = request.GET.get('year', '')
    if year_filter:
        students = students.filter(admission_year=year_filter)
    session_filter = request.GET.get('session', '')
    if session_filter:
        students = students.filter(session=session_filter)
    clearance_filter = request.GET.get('clearance', '')
    if clearance_filter == 'has_clearance':
        students = students.filter(graduation_clearance__isnull=False)
    elif clearance_filter == 'no_clearance':
        students = students.filter(graduation_clearance__isnull=True)
    elif clearance_filter == 'cleared':
        students = students.filter(graduation_clearance__all_requirements_met=True)
    elif clearance_filter == 'pending':
        students = students.filter(graduation_clearance__all_requirements_met=False)
    paginator = Paginator(students, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    from .models import Program
    programs = Program.objects.all()
    years = Student.objects.values_list('admission_year', flat=True).distinct().order_by('-admission_year')
    sessions = Student.SESSION_CHOICES
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'program_filter': program_filter,
        'year_filter': year_filter,
        'session_filter': session_filter,
        'clearance_filter': clearance_filter,
        'programs': programs,
        'years': years,
        'sessions': sessions,
        'total_count': students.count()
    }
    return render(request, 'student_registration/select_student_for_grad_clearance.html', context)

@login_required
def graduation_clearance_create(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    try:
        existing_clearance = student.graduation_clearance
        messages.info(request, f'Graduation clearance already exists for {student.name}. Redirecting to edit.')
        return redirect('pass_book:graduation_clearance_edit', student_pk=student.pk)
    except GraduationClearance.DoesNotExist:
        pass
    if request.method == 'POST':
        form = GraduationClearanceForm(request.POST, request.FILES)
        if form.is_valid():
            clearance = form.save(commit=False)
            clearance.student = student
            clearance.save()
            messages.success(request, f'Graduation clearance created successfully for {student.name}!')
            return redirect('pass_book:graduation_clearance_detail', student_pk=student.pk)
    else:
        form = GraduationClearanceForm()
    context = {
        'form': form,
        'student': student,
        'action': 'Create'
    }
    return render(request, 'student_registration/grad_clearance_form.html', context)

@login_required
def graduation_clearance_edit(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    clearance = get_object_or_404(GraduationClearance, student=student)
    if request.method == 'POST':
        form = GraduationClearanceForm(request.POST, request.FILES, instance=clearance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Graduation clearance updated successfully for {student.name}!')
            return redirect('graduation_clearance_detail', student_pk=student.pk)
    else:
        form = GraduationClearanceForm(instance=clearance)
    context = {
        'form': form,
        'student': student,
        'clearance': clearance,
        'action': 'Edit'
    }
    return render(request, 'student_registration/grad_clearance_form.html', context)

@login_required
def graduation_clearance_detail(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    clearance = get_object_or_404(GraduationClearance, student=student)
    context = {
        'student': student,
        'clearance': clearance
    }
    return render(request, 'student_registration/grad_clearance_detail.html', context)

@login_required
def graduation_clearance_delete(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    clearance = get_object_or_404(GraduationClearance, student=student)
    if request.method == 'POST':
        # Allow Academic Registrar or Sysadmin to delete graduation clearances
        if not (request.user.is_academic_registrar or request.user.is_sysadmin):
            raise PermissionDenied("Only Academic Registrar or System Administrator can delete graduation clearances.")
        student_name = student.name
        clearance.delete()
        messages.success(request, f'Graduation clearance deleted successfully for {student_name}!')
        return redirect('pass_book:student_selection_view')
    context = {
        'student': student,
        'clearance': clearance
    }
    return render(request, 'student_registration/grad_clearance_delete.html', context)

@login_required
def graduation_certificate_view(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    clearance = get_object_or_404(GraduationClearance, student=student)
    if not clearance.all_requirements_met:
        messages.error(request, 'Student has not met all graduation requirements!')
        return redirect('graduation_clearance_detail', student_pk=student.pk)
    context = {
        'student': student,
        'clearance': clearance
    }
    return render(request, 'student_registration/grad_clearance_certificate.html', context)

@login_required
def bulk_clearance_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        student_ids = request.POST.getlist('student_ids')
        if not student_ids:
            messages.error(request, 'No students selected!')
            return redirect('pass_book:student_selection_view')
        # Allow Academic Registrar or Sysadmin for bulk actions
        if not (request.user.is_academic_registrar or request.user.is_sysadmin):
            raise PermissionDenied("Only Academic Registrar or System Administrator can perform bulk clearance actions.")
        students = Student.objects.filter(pk__in=student_ids)
        if action == 'create_clearances':
            created_count = 0
            for student in students:
                clearance, created = GraduationClearance.objects.get_or_create(
                    student=student,
                    defaults={'all_requirements_met': False}
                )
                if created:
                    created_count += 1
            messages.success(request, f'Created {created_count} graduation clearance records!')
        elif action == 'mark_cleared':
            updated = GraduationClearance.objects.filter(
                student__in=students
            ).update(
                all_requirements_met=True,
                clearance_date=timezone.now().date()
            )
            messages.success(request, f'Marked {updated} students as cleared!')
        elif action == 'mark_pending':
            updated = GraduationClearance.objects.filter(
                student__in=students
            ).update(
                all_requirements_met=False,
                clearance_date=None
            )
            messages.success(request, f'Marked {updated} students as pending!')
    return redirect('pass_book:student_selection_view')

# ============================================================================
# AJAX AND API VIEWS
# ============================================================================

@csrf_exempt
def student_search_api(request):
    if request.method == 'GET':
        query = request.GET.get('q', '')
        students = Student.objects.filter(
            Q(name__icontains=query) | Q(registration_number__icontains=query)
        )[:10]
        results = [
            {
                'id': student.id,
                'name': student.name,
                'registration_number': student.registration_number,
                'programme': student.programme
            }
            for student in students
        ]
        return JsonResponse({'results': results})
    return JsonResponse({'error': 'Invalid request method'})

@login_required
def access_number_check_api(request):
    access_number = request.GET.get('access_number', '')
    exists = AccessNumber.objects.filter(access_number=access_number).exists()
    return JsonResponse({'exists': exists})

@login_required
def student_statistics_api(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    stats = {
        'static_access_number': student.static_access_number,
        'total_access_numbers': student.access_numbers.count(),
        'completed_registrations': SemesterRegistration.objects.filter(
            access_number__student=student,
            finance_cleared=True,
            academic_cleared=True,
            orientation_cleared=True,
            assimilation_cleared=True
        ).count(),
        'total_course_units': StudentCourseUnit.objects.filter(
            access_number__student=student
        ).count(),
        'passed_course_units': StudentCourseUnit.objects.filter(
            access_number__student=student,
            status='PASSED'
        ).count(),
        'total_course_works': StudentCourseWork.objects.filter(
            access_number__student=student
        ).count(),
        'completed_course_works': StudentCourseWork.objects.filter(
            access_number__student=student,
            status='DONE'
        ).count(),
        'association_memberships': StudentAssociation.objects.filter(
            access_number__student=student,
            status='ACTIVE'
        ).count(),
        'has_laptop_scheme': hasattr(student, 'laptop_scheme'),
        'has_graduation_clearance': hasattr(student, 'graduation_clearance'),
        'academic_program': {
            'name': student.program.name if student.program else '',
            'faculty': student.program.faculty if student.program else '',
            'duration': student.program.duration if student.program else 0
        }
    }
    return JsonResponse(stats)

# ============================================================================
# REPORT VIEWS
# ============================================================================

from django.utils import timezone
# ...
#context['utc_now'] = timezone.now()  # This is timezone-aware


@login_required
def reports_dashboard_view(request):
    """Reports dashboard with various statistics"""
    # === 1. Students by Faculty ===
    students_by_faculty = Student.objects.values(
        faculty_name=F('program__faculty')
    ).annotate(
        count=Count('*')
    ).order_by('-count')
    # === 2. Students by Programme (Top 10) ===
    students_by_programme = Student.objects.values(
        programme_name=F('program__name')
    ).annotate(
        count=Count('*')
    ).order_by('-count')[:10]
    # Pre-calculate percentage for progress bars
    students_by_programme_with_percent = []
    if students_by_programme:
        # Convert to list to allow indexing
        students_by_programme_list = list(students_by_programme)
        max_count = students_by_programme_list[0]['count']  # Top programme count
        for item in students_by_programme_list:
            percentage = (item['count'] / max_count * 100) if max_count > 0 else 0
            item['percentage'] = min(100.0, round(percentage, 1))  # Cap at 100%
            students_by_programme_with_percent.append(item)
    # else: remains empty list
    # === 3. Registrations by Semester ===
    registrations_by_semester = SemesterRegistration.objects.select_related(
        'access_number__semester'
    ).values('access_number__semester__number').annotate(
        count=Count('*')
    ).order_by('access_number__semester__number')
    # === 4. Laptop Scheme Stats ===
    laptop_aggregates = BbalaLaptopScheme.objects.aggregate(
        total_payments=Sum('payment_made'),
        total_balance=Sum('balance')
    )
    laptop_scheme_stats = {
        'total_participants': BbalaLaptopScheme.objects.count(),
        'total_payments': float(laptop_aggregates['total_payments'] or 0),
        'total_balance': float(laptop_aggregates['total_balance'] or 0),
    }
    # === 5. Clearance Stats ===
    clearance_stats = {
        'semester_clearances': SemesterClearance.objects.filter(
            finance_cleared=True, academic_cleared=True
        ).count(),
        'graduation_clearances': GraduationClearance.objects.filter(
            all_requirements_met=True
        ).count()
    }
    # === Build Context ===
    context = {
        
        'students_by_faculty': students_by_faculty,
        'students_by_programme': students_by_programme_with_percent,
        'registrations_by_semester': registrations_by_semester,
        'laptop_scheme_stats': laptop_scheme_stats,
        'clearance_stats': clearance_stats,
    }
    context['utc_now'] = timezone.now()  # This is timezone-aware
    return render(request, 'student_registration/reports/reports_dashboard.html', context)

from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Count, Q, Sum, Case, When, IntegerField, Avg
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

class StudentReportView(LoginRequiredMixin, ListView):
    """
    BUSINESS REPORT: Comprehensive Student List
    Used for: General student lookup, contact info, program enrollment.
    """
    model = Student
    template_name = 'student_registration/reports/student_report.html'
    context_object_name = 'students'
    paginate_by = 30  # Optimized for printing
    def get_queryset(self):
        queryset = Student.objects.select_related('program').order_by('name')
        # Filters
        program_id = self.request.GET.get('program')
        session = self.request.GET.get('session')
        admission_year = self.request.GET.get('admission_year')
        if program_id:
            queryset = queryset.filter(program_id=program_id)
        if session:
            queryset = queryset.filter(session=session)
        if admission_year:
            queryset = queryset.filter(admission_year=admission_year)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['programs'] = Program.objects.filter(is_active=True)
        context['sessions'] = Student.SESSION_CHOICES
        context['years'] = Student.objects.values_list('admission_year', flat=True).distinct().order_by('-admission_year')
        context['report_title'] = "Student Master List"
        context['utc_now'] = timezone.now()  # This is timezone-aware
        return context

class ProgramEnrollmentReportView(LoginRequiredMixin, ListView):
    """
    BUSINESS REPORT: Program Enrollment Summary
    Used for: Resource allocation, faculty planning, budgeting.
    """
    model = Program
    template_name = 'student_registration/reports/program_enrollment_report.html'
    context_object_name = 'programs'
    def get_queryset(self):
        year_id = self.request.GET.get('academic_year')
        if year_id:
            academic_year = AcademicYear.objects.get(id=year_id)
        else:
            academic_year = AcademicYear.objects.filter(is_active=True).first()
        programs = Program.objects.filter(is_active=True).annotate(
            student_count=Count(
                'students__access_numbers',
                filter=Q(students__access_numbers__academic_year=academic_year)
            )
        ).order_by('-student_count')
        self.extra_context = {
            'selected_year': academic_year,
            'academic_years': AcademicYear.objects.all().order_by('-start_date'),
            'report_title': f"Program Enrollment for {academic_year.year_label if academic_year else 'All Years'}"
        }
        return programs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['selected_year'] = self.extra_context.get('selected_year')
        context['academic_years'] = self.extra_context.get('academic_years')
        context['report_title'] = self.extra_context.get('report_title')
        context['total_students'] = sum(p.student_count for p in context['programs'])
        context['utc_now'] = timezone.now()  # This is timezone-aware
        return context

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch, Count, Case, When, IntegerField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import (
    SemesterRegistration, 
    SemesterClearance, 
    Semester, 
    AccessNumber,
    Student
)


@login_required
def semester_clearance_report(request):
    """
    BUSINESS REPORT: Semester Clearance Status
    Used for: Identifying students who haven't cleared fees or academic holds.
    Critical for semester commencement.
    """
    
    # Get filter parameters
    semester_id = request.GET.get('semester')
    finance_filter = request.GET.get('finance_cleared')
    academic_filter = request.GET.get('academic_cleared')
    orientation_filter = request.GET.get('orientation_cleared')
    assimilation_filter = request.GET.get('assimilation_cleared')
    search_query = request.GET.get('search', '').strip()
    
    # Initialize context
    context = {
        'now': timezone.now(),
        'utc_now': timezone.now(),
        'report_title': "Semester Clearance Report",
        'semesters': Semester.objects.select_related('academic_year').filter(
            is_active=True
        ).order_by('-start_date'),
    }
    
    # If no semester selected, show empty state
    if not semester_id:
        context['registrations'] = []
        context['show_empty_state'] = True
        return render(request, 'student_registration/reports/semester_clearance_report.html', context)
    
    # Get the selected semester
    semester = get_object_or_404(Semester, id=semester_id)
    context['selected_semester'] = semester
    
    # Base queryset - get all registrations for the semester
    queryset = SemesterRegistration.objects.filter(
        access_number__semester=semester
    ).select_related(
        'access_number__student',
        'access_number__student__program',
        'access_number__semester',
        'access_number__academic_year'
    ).prefetch_related(
        Prefetch(
            'access_number__clearance',
            queryset=SemesterClearance.objects.all()
        )
    )
    
    # Apply search filter
    if search_query:
        queryset = queryset.filter(
            Q(access_number__student__name__icontains=search_query) |
            Q(access_number__student__registration_number__icontains=search_query) |
            Q(access_number__access_number__icontains=search_query) |
            Q(access_number__student__student_contact__icontains=search_query)
        )
    
    # Apply finance clearance filter
    if finance_filter == 'True':
        # Only students with clearance record AND finance cleared
        queryset = queryset.filter(
            access_number__clearance__finance_cleared=True
        )
    elif finance_filter == 'False':
        # Students without clearance OR finance not cleared
        queryset = queryset.filter(
            Q(access_number__clearance__isnull=True) |
            Q(access_number__clearance__finance_cleared=False)
        )
    elif finance_filter == 'no_record':
        # Only students without clearance record
        queryset = queryset.filter(access_number__clearance__isnull=True)
    
    # Apply academic clearance filter
    if academic_filter == 'True':
        queryset = queryset.filter(
            access_number__clearance__academic_cleared=True
        )
    elif academic_filter == 'False':
        queryset = queryset.filter(
            Q(access_number__clearance__isnull=True) |
            Q(access_number__clearance__academic_cleared=False)
        )
    elif academic_filter == 'no_record':
        queryset = queryset.filter(access_number__clearance__isnull=True)
    
    # Apply orientation filter (from SemesterRegistration)
    if orientation_filter == 'True':
        queryset = queryset.filter(orientation_cleared=True)
    elif orientation_filter == 'False':
        queryset = queryset.filter(orientation_cleared=False)
    
    # Apply assimilation filter (from SemesterRegistration)
    if assimilation_filter == 'True':
        queryset = queryset.filter(assimilation_cleared=True)
    elif assimilation_filter == 'False':
        queryset = queryset.filter(assimilation_cleared=False)
    
    # Order by student name
    queryset = queryset.order_by('access_number__student__name')
    
    # Calculate statistics BEFORE pagination
    total_students = queryset.count()
    
    # Count students with clearance records
    students_with_clearance = queryset.filter(
        access_number__clearance__isnull=False
    ).count()
    
    # Count cleared students
    finance_cleared_count = queryset.filter(
        access_number__clearance__finance_cleared=True
    ).count()
    
    academic_cleared_count = queryset.filter(
        access_number__clearance__academic_cleared=True
    ).count()
    
    orientation_cleared_count = queryset.filter(
        orientation_cleared=True
    ).count()
    
    assimilation_cleared_count = queryset.filter(
        assimilation_cleared=True
    ).count()
    
    # Count fully cleared students (all 4 clearances)
    fully_cleared_count = queryset.filter(
        access_number__clearance__finance_cleared=True,
        access_number__clearance__academic_cleared=True,
        orientation_cleared=True,
        assimilation_cleared=True
    ).count()
    
    # Count students without clearance records
    no_clearance_record = queryset.filter(
        access_number__clearance__isnull=True
    ).count()
    
    # Add statistics to context
    context.update({
        'total_students': total_students,
        'students_with_clearance': students_with_clearance,
        'finance_cleared_count': finance_cleared_count,
        'academic_cleared_count': academic_cleared_count,
        'orientation_cleared_count': orientation_cleared_count,
        'assimilation_cleared_count': assimilation_cleared_count,
        'fully_cleared_count': fully_cleared_count,
        'no_clearance_record': no_clearance_record,
        
        # Percentages
        'finance_cleared_percent': (finance_cleared_count / total_students * 100) if total_students > 0 else 0,
        'academic_cleared_percent': (academic_cleared_count / total_students * 100) if total_students > 0 else 0,
        'orientation_cleared_percent': (orientation_cleared_count / total_students * 100) if total_students > 0 else 0,
        'assimilation_cleared_percent': (assimilation_cleared_count / total_students * 100) if total_students > 0 else 0,
        'fully_cleared_percent': (fully_cleared_count / total_students * 100) if total_students > 0 else 0,
    })
    
    # Pagination
    paginator = Paginator(queryset, 50)  # Show 50 records per page
    page = request.GET.get('page', 1)
    
    try:
        registrations = paginator.page(page)
    except PageNotAnInteger:
        registrations = paginator.page(1)
    except EmptyPage:
        registrations = paginator.page(paginator.num_pages)
    
    context['registrations'] = registrations
    context['show_empty_state'] = False
    
    # Add filter values to context for form persistence
    context['filters'] = {
        'semester': semester_id,
        'finance_cleared': finance_filter,
        'academic_cleared': academic_filter,
        'orientation_cleared': orientation_filter,
        'assimilation_cleared': assimilation_filter,
        'search': search_query,
    }
    
    return render(request, 'student_registration/reports/semester_clearance_report.html', context)


@login_required
def create_clearance_records_for_semester(request, semester_id):
    """
    Utility view to create SemesterClearance records for all students in a semester
    who don't have one yet.
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('student_registration:semester_clearance_report')
    
    semester = get_object_or_404(Semester, id=semester_id)
    
    # Get all access numbers for this semester
    access_numbers = AccessNumber.objects.filter(semester=semester)
    
    created_count = 0
    for access_number in access_numbers:
        _, created = SemesterClearance.objects.get_or_create(
            access_number=access_number
        )
        if created:
            created_count += 1
    
    if created_count > 0:
        messages.success(
            request, 
            f"Successfully created {created_count} clearance record(s) for {semester}."
        )
    else:
        messages.info(
            request, 
            f"All students in {semester} already have clearance records."
        )
    
    return redirect(f"{request.META.get('HTTP_REFERER', 'student_registration:semester_clearance_report')}?semester={semester_id}")


@login_required
def export_clearance_report_csv(request):
    """Export clearance report to CSV"""
    import csv
    from django.http import HttpResponse
    
    semester_id = request.GET.get('semester')
    if not semester_id:
        return HttpResponse("No semester selected", status=400)
    
    semester = get_object_or_404(Semester, id=semester_id)
    
    # Get all registrations (without pagination)
    registrations = SemesterRegistration.objects.filter(
        access_number__semester=semester
    ).select_related(
        'access_number__student',
        'access_number__student__program',
        'access_number__clearance'
    ).order_by('access_number__student__name')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="clearance_report_{semester.semester_code}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Access Number',
        'Student Name',
        'Program',
        'Contact',
        'Finance Cleared',
        'Finance Officer',
        'Finance Date',
        'Academic Cleared',
        'Academic Officer',
        'Academic Date',
        'Orientation Cleared',
        'Assimilation Cleared',
        'All Cleared'
    ])
    
    # Write data rows
    for reg in registrations:
        clearance = getattr(reg.access_number, 'clearance', None)
        
        all_cleared = (
            clearance and clearance.finance_cleared and 
            clearance.academic_cleared and 
            reg.orientation_cleared and 
            reg.assimilation_cleared
        ) if clearance else False
        
        writer.writerow([
            reg.access_number.access_number,
            reg.access_number.student.name,
            reg.access_number.student.program.name,
            reg.access_number.student.student_contact,
            'Yes' if clearance and clearance.finance_cleared else 'No',
            clearance.finance_officer_name if clearance else '',
            clearance.finance_clearance_date.strftime('%Y-%m-%d') if clearance and clearance.finance_clearance_date else '',
            'Yes' if clearance and clearance.academic_cleared else 'No',
            clearance.academic_officer_name if clearance else '',
            clearance.academic_clearance_date.strftime('%Y-%m-%d') if clearance and clearance.academic_clearance_date else '',
            'Yes' if reg.orientation_cleared else 'No',
            'Yes' if reg.assimilation_cleared else 'No',
            'Yes' if all_cleared else 'No'
        ])
    
    return response

class SemesterClearanceReportView(LoginRequiredMixin, ListView):
    """
    BUSINESS REPORT: Semester Clearance Status
    Used for: Identifying students who haven't cleared fees or academic holds.
    Critical for semester commencement.
    """
    model = SemesterRegistration
    template_name = 'student_registration/reports/semester_clearance_report.html'
    context_object_name = 'registrations'
    paginate_by = 50

    def get_queryset(self):
        semester_id = self.request.GET.get('semester')
        
        if semester_id:
            semester = Semester.objects.get(id=semester_id)
            queryset = SemesterRegistration.objects.filter(
                access_number__semester=semester
            ).select_related(
                'access_number__student',
                'access_number__semester',
                'access_number__academic_year'
            ).prefetch_related(
                'access_number__clearance'  # Use prefetch since it's OneToOne with possible None
            ).order_by('access_number__student__name')
        else:
            queryset = SemesterRegistration.objects.none()

        # Filter by clearance status
        finance_filter = self.request.GET.get('finance_cleared')
        academic_filter = self.request.GET.get('academic_cleared')
        
        if finance_filter == 'True':
            # Show only students WITH clearance record AND finance cleared
            queryset = queryset.filter(
                access_number__clearance__finance_cleared=True
            )
        elif finance_filter == 'False':
            # Show students either WITHOUT clearance record OR with finance NOT cleared
            from django.db.models import Q
            queryset = queryset.filter(
                Q(access_number__clearance__isnull=True) |
                Q(access_number__clearance__finance_cleared=False)
            )
        
        if academic_filter == 'True':
            queryset = queryset.filter(
                access_number__clearance__academic_cleared=True
            )
        elif academic_filter == 'False':
            from django.db.models import Q
            queryset = queryset.filter(
                Q(access_number__clearance__isnull=True) |
                Q(access_number__clearance__academic_cleared=False)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['semesters'] = Semester.objects.select_related('academic_year').filter(
            is_active=True
        ).order_by('-start_date')
        context['report_title'] = "Semester Clearance Report"
        context['utc_now'] = timezone.now()
        
        # Add summary statistics
        if self.get_queryset().exists():
            registrations = self.get_queryset()
            context['total_students'] = registrations.count()
            context['finance_cleared_count'] = registrations.filter(
                access_number__clearance__finance_cleared=True
            ).count()
            context['academic_cleared_count'] = registrations.filter(
                access_number__clearance__academic_cleared=True
            ).count()
            context['no_clearance_record'] = registrations.filter(
                access_number__clearance__isnull=True
            ).count()
        
        return context

class StudentCourseUnitReportView(LoginRequiredMixin, ListView):
    """
    BUSINESS REPORT: Course Unit Registration & Status
    Used for: Academic advising, identifying students at risk (retakes/missed), HOD reporting.
    """
    model = StudentCourseUnit
    template_name = 'student_registration/reports/student_course_unit_report.html'
    context_object_name = 'course_registrations'
    paginate_by = 50
    def get_queryset(self):
        semester_id = self.request.GET.get('semester')
        status_filter = self.request.GET.get('status')
        course_unit_id = self.request.GET.get('course_unit')
        queryset = StudentCourseUnit.objects.select_related(
            'access_number__student',
            'access_number__semester',
            'course_unit'
        ).order_by('access_number__student__name', 'course_unit__code')
        if semester_id:
            queryset = queryset.filter(access_number__semester_id=semester_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if course_unit_id:
            queryset = queryset.filter(course_unit_id=course_unit_id)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['semesters'] = Semester.objects.select_related('academic_year').all().order_by('-start_date')
        context['statuses'] = StudentCourseUnit.STATUS_CHOICES
        context['course_units'] = CourseUnit.objects.filter(is_active=True).order_by('code')
        context['report_title'] = "Student Course Unit Status Report"
        context['utc_now'] = timezone.now()  # This is timezone-aware
        return context

class FinanceReceivablesReportView(LoginRequiredMixin, ListView):
    """
    BUSINESS REPORT: Bbala Laptop Scheme Receivables
    Used for: Finance department to track outstanding payments.
    """
    model = BbalaLaptopScheme
    template_name = 'student_registration/reports/finance_report.html'
    context_object_name = 'schemes'
    paginate_by = 50
    def get_queryset(self):
        # Show only students with a balance > 0
        queryset = BbalaLaptopScheme.objects.filter(
            balance__gt=0
        ).select_related('student__program').order_by('-balance')
        # Filter by program
        program_id = self.request.GET.get('program')
        if program_id:
            queryset = queryset.filter(student__program_id=program_id)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['programs'] = Program.objects.filter(is_active=True)
        context['total_receivable'] = BbalaLaptopScheme.objects.aggregate(total=Sum('balance'))['total'] or 0
        context['report_title'] = "Laptop Scheme - Outstanding Receivables"
        context['utc_now'] = timezone.now()  # This is timezone-aware
        return context

class GraduationEligibilityReportView(LoginRequiredMixin, ListView):
    """
    BUSINESS REPORT: Graduation Eligibility
    Used for: Graduation committee to identify eligible students.
    Checks: All coursework done, internship done, no dead semesters pending, graduation clearance not yet issued.
    """
    model = Student
    template_name = 'student_registration/reports/graduation_eligibility_report.html'
    context_object_name = 'students'
    paginate_by = 50
    def get_queryset(self):
        # Get students in their final year (assumes 4-year program, adjust logic as needed)
        final_year_students = Student.objects.filter(
            expected_graduation_year__lte=timezone.now().year
        ).select_related('program')
        eligible_students = []
        for student in final_year_students:
            # Check 1: No pending Graduation Clearance (i.e., not already graduated)
            if hasattr(student, 'graduation_clearance'):
                continue
            # Check 2: All coursework for all semesters is 'DONE' or 'PASSED'
            all_coursework_done = StudentCourseWork.objects.filter(
                access_number__student=student,
                status='MISSED'
            ).exists()
            if all_coursework_done:
                continue
            all_course_units_passed = StudentCourseUnit.objects.filter(
                access_number__student=student,
                status__in=['MISSED', 'RETAKE']
            ).exists()
            if all_course_units_passed:
                continue
            # Check 3: Internship is marked as 'DONE'
            internship_done = Internship.objects.filter(
                access_number__student=student,
                status='DONE'
            ).exists()
            if not internship_done:
                continue
            # Check 4: No pending Dead Semester applications
            pending_dead_sem = DeadSemesterApplication.objects.filter(
                student=student,
                approved=False
            ).exists()
            if pending_dead_sem:
                continue
            eligible_students.append(student.id)
        queryset = Student.objects.filter(
            id__in=eligible_students
        ).select_related('program').order_by('name')
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['report_title'] = "Graduation Eligibility Report"
        context['utc_now'] = timezone.now()  # This is timezone-aware
        return context


# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, Count, Case, When, Value, BooleanField
from django.http import HttpResponseForbidden
from datetime import date

from .models import (
    Student, AccessNumber, Semester, AcademicYear, 
    SemesterClearance, SemesterRegistration,
    StudentCourseUnit, StudentCourseWork,
    MedicalRegistration, NCHERegistration, Internship,
    BbalaLaptopScheme, DeadSemesterApplication, ResumptionApplication
)
# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, Count, Case, When, Value, BooleanField
from django.http import HttpResponseForbidden, JsonResponse
from datetime import date
from django.apps import apps

 
@login_required
def semester_clearance_view(request, academic_year_id=None, semester_id=None):
    """
    Simplified semester clearance view with search functionality for semesters.
    """
    
    # Get current academic year and semester if not specified
    current_academic_year = AcademicYear.objects.filter(is_active=True).first()
    current_semester = Semester.objects.filter(is_active=True).first()
    
    # Use provided parameters or defaults
    academic_year = get_object_or_404(AcademicYear, pk=academic_year_id) if academic_year_id else current_academic_year
    semester = get_object_or_404(Semester, pk=semester_id) if semester_id else current_semester
    
    if not academic_year or not semester:
        # Handle case where no active academic year or semester exists
        academic_year = AcademicYear.objects.order_by('-start_date').first()
        semester = Semester.objects.order_by('-start_date').first()
        
        if not academic_year or not semester:
            # If still no academic year or semester, create empty context
            context = {
                'students_data': [],
                'academic_year': None,
                'semester': None,
                'academic_years': AcademicYear.objects.all().order_by('-start_date'),
                'semesters': Semester.objects.all().order_by('number'),
                'total_students': 0,
                'fully_cleared': 0,
                'pending_clearance': 0,
                'is_finance_officer': False,
                'is_academic_officer': False,
                'is_supervisor': request.user.is_superuser or request.user.is_staff,
                'current_date': date.today(),
            }
            return render(request, 'pass_book:semester_clearance.html', context)
    
    # Check user permissions
    user = request.user
    is_finance_officer = user.groups.filter(name='Finance').exists() or user.has_perm('pass_book.can_clear_finance')
    is_academic_officer = user.groups.filter(name='Academic').exists() or user.has_perm('pass_book.can_clear_academic')
    is_supervisor = user.is_superuser or user.is_staff
    
    # Get all access numbers for the selected semester
    access_numbers = AccessNumber.objects.filter(
        academic_year=academic_year,
        semester=semester,
        is_active=True
    ).select_related(
        'student',
        'semester',
        'academic_year'
    ).prefetch_related(
        'semester_registration',
        'clearance'
    )
    
    # Filter based on user role
    if is_finance_officer:
        # Finance officers see all but can only manage finance clearance
        pass
    elif is_academic_officer:
        # Academic officers see all but can only manage academic clearance
        pass
    elif not is_supervisor:
        # Regular users only see their own data
        if hasattr(user, 'student_profile'):
            access_numbers = access_numbers.filter(student=user.student_profile)
        else:
            return HttpResponseForbidden("You don't have access to this page.")
    
    # Get all clearance records for this semester
    clearance_records = SemesterClearance.objects.filter(
        access_number__in=access_numbers
    ).select_related('access_number__student')
    
    # Create a dictionary for quick lookup
    clearance_dict = {record.access_number_id: record for record in clearance_records}
    
    # Prepare student data with clearance status
    students_data = []
    
    for access_num in access_numbers:
        student = access_num.student
        clearance_record = clearance_dict.get(access_num.access_number)
        
        # Get semester registration
        semester_reg = getattr(access_num, 'semester_registration', None)
        
        # Build student data dictionary
        student_data = {
            'student': student,
            'access_number': access_num,
            'semester': semester,
            'academic_year': academic_year,
            'semester_registration': semester_reg,
            'clearance_record': clearance_record,
            'finance_cleared': clearance_record.finance_cleared if clearance_record else False,
            'academic_cleared': clearance_record.academic_cleared if clearance_record else False,
            'fully_cleared': clearance_record and clearance_record.finance_cleared and clearance_record.academic_cleared if clearance_record else False,
            'finance_clearance_date': clearance_record.finance_clearance_date if clearance_record else None,
            'academic_clearance_date': clearance_record.academic_clearance_date if clearance_record else None,
            'finance_officer_name': clearance_record.finance_officer_name if clearance_record else None,
            'academic_officer_name': clearance_record.academic_officer_name if clearance_record else None,
        }
        
        students_data.append(student_data)
    
    # Calculate statistics
    total_students = len(students_data)
    fully_cleared = sum(1 for s in students_data if s['fully_cleared'])
    pending_clearance = total_students - fully_cleared
    
    context = {
        'students_data': students_data,
        'academic_year': academic_year,
        'semester': semester,
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
        'semesters': Semester.objects.all().order_by('number'),
        'total_students': total_students,
        'fully_cleared': fully_cleared,
        'pending_clearance': pending_clearance,
        'is_finance_officer': is_finance_officer,
        'is_academic_officer': is_academic_officer,
        'is_supervisor': is_supervisor,
        'current_date': date.today(),
    }
    
    return render(request, 'student_registration/reports/semester_clearance.html', context)


@login_required
def update_clearance_status(request, access_number):
    """
    Update clearance status for a specific student.
    This view handles both finance and academic clearance updates.
    """
    if request.method == 'POST':
        # Get the access number object
        access_num = get_object_or_404(AccessNumber, access_number=access_number)
        
        # Check user permissions
        user = request.user
        is_finance_officer = user.groups.filter(name='Finance').exists() or user.has_perm('pass_book.can_clear_finance')
        is_academic_officer = user.groups.filter(name='Academic').exists() or user.has_perm('pass_book.can_clear_academic')
        is_supervisor = user.is_superuser or user.is_staff
        
        # Get or create clearance record
        clearance, created = SemesterClearance.objects.get_or_create(
            access_number=access_num,
            defaults={
                'finance_cleared': False,
                'academic_cleared': False,
            }
        )
        
        # Update based on user role
        updated = False
        
        if 'finance_cleared' in request.POST and (is_finance_officer or is_supervisor):
            clearance.finance_cleared = request.POST.get('finance_cleared') == 'true'
            clearance.finance_officer_name = user.get_full_name() or user.username
            clearance.finance_officer_designation = 'Finance Officer'
            clearance.finance_clearance_date = date.today()
            updated = True
        
        if 'academic_cleared' in request.POST and (is_academic_officer or is_supervisor):
            clearance.academic_cleared = request.POST.get('academic_cleared') == 'true'
            clearance.academic_officer_name = user.get_full_name() or user.username
            clearance.academic_officer_designation = 'Academic Officer'
            clearance.academic_clearance_date = date.today()
            updated = True
        
        if updated:
            clearance.save()
            
            # Return success response
            return JsonResponse({
                'success': True,
                'message': 'Clearance status updated successfully',
                'finance_cleared': clearance.finance_cleared,
                'academic_cleared': clearance.academic_cleared,
                'fully_cleared': clearance.finance_cleared and clearance.academic_cleared,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to update this clearance'
            }, status=403)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)




@login_required
#@permission_required('pass_book.change_semesterclearance', raise_exception=True)
def update_clearance_status(request, access_number):
    """
    Update clearance status for a specific student.
    This view handles both finance and academic clearance updates.
    """
    if request.method == 'POST':
        # Get the access number object
        access_num = get_object_or_404(AccessNumber, access_number=access_number)
        
        # Check user permissions
        user = request.user
        is_finance_officer = user.groups.filter(name='Finance').exists() or user.has_perm('pass_book.can_clear_finance')
        is_academic_officer = user.groups.filter(name='Academic').exists() or user.has_perm('pass_book.can_clear_academic')
        is_supervisor = user.is_superuser or user.is_staff
        
        # Get or create clearance record
        clearance, created = SemesterClearance.objects.get_or_create(
            access_number=access_num,
            defaults={
                'finance_cleared': False,
                'academic_cleared': False,
            }
        )
        
        # Update based on user role
        updated = False
        
        if 'finance_cleared' in request.POST and (is_finance_officer or is_supervisor):
            clearance.finance_cleared = request.POST.get('finance_cleared') == 'true'
            clearance.finance_officer_name = user.get_full_name() or user.username
            clearance.finance_officer_designation = 'Finance Officer'
            clearance.finance_clearance_date = date.today()
            updated = True
        
        if 'academic_cleared' in request.POST and (is_academic_officer or is_supervisor):
            clearance.academic_cleared = request.POST.get('academic_cleared') == 'true'
            clearance.academic_officer_name = user.get_full_name() or user.username
            clearance.academic_officer_designation = 'Academic Officer'
            clearance.academic_clearance_date = date.today()
            updated = True
        
        if updated:
            clearance.save()
            
            # Log the action
            from django.contrib.admin.models import LogEntry, CHANGE
            from django.contrib.contenttypes.models import ContentType
            
            LogEntry.objects.log_action(
                user_id=user.id,
                content_type_id=ContentType.objects.get_for_model(clearance).pk,
                object_id=clearance.pk,
                object_repr=str(clearance),
                action_flag=CHANGE,
                change_message=f"Updated clearance status"
            )
            
            # Return success response
            return JsonResponse({
                'success': True,
                'message': 'Clearance status updated successfully',
                'finance_cleared': clearance.finance_cleared,
                'academic_cleared': clearance.academic_cleared,
                'fully_cleared': clearance.finance_cleared and clearance.academic_cleared,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to update this clearance'
            }, status=403)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
#@permission_required('pass_book.view_semesterclearance', raise_exception=True)
def clearance_summary_report(request, academic_year_id=None, semester_id=None):
    """
    Generate a summary report of clearance status for any academic year and semester.
    """
    # Get parameters - allow any academic year and semester
    academic_year = get_object_or_404(AcademicYear, pk=academic_year_id) if academic_year_id else None
    semester = get_object_or_404(Semester, pk=semester_id) if semester_id else None
    
    if not academic_year or not semester:
        # Use current active if not specified
        academic_year = AcademicYear.objects.filter(is_active=True).first()
        semester = Semester.objects.filter(is_active=True).first()
        
        if not academic_year or not semester:
            # If still no academic year or semester, use most recent
            academic_year = AcademicYear.objects.order_by('-start_date').first()
            semester = Semester.objects.order_by('-start_date').first()  # Changed from '-created_at' to '-start_date'
    
    if not academic_year or not semester:
        # Final fallback - empty report
        context = {
            'academic_year': None,
            'semester': None,
            'program_stats': [],
            'totals': {
                'total_students': 0,
                'fully_cleared': 0,
                'finance_cleared': 0,
                'academic_cleared': 0,
                'pending': 0,
            },
            'generated_date': date.today(),
            'generated_by': request.user.get_full_name() or request.user.username,
        }
        return render(request, 'clearance_summary_report.html', context)
    
    # Get all access numbers for the selected academic year and semester
    access_numbers = AccessNumber.objects.filter(
        academic_year=academic_year,
        semester=semester,
        is_active=True
    ).select_related('student__program')
    
    # Get clearance records
    clearance_records = SemesterClearance.objects.filter(
        access_number__in=access_numbers
    ).select_related('access_number__student__program')
    
    # Group by program
    program_stats = {}
    
    for access_num in access_numbers:
        if hasattr(access_num.student, 'program'):
            program_code = access_num.student.program.code
            program_name = access_num.student.program.name
            
            if program_code not in program_stats:
                program_stats[program_code] = {
                    'name': program_name,
                    'total': 0,
                    'fully_cleared': 0,
                    'finance_cleared': 0,
                    'academic_cleared': 0,
                    'pending': 0,
                }
            
            program_stats[program_code]['total'] += 1
            
            # Get clearance status
            try:
                clearance = clearance_records.get(access_number=access_num)
                if clearance.finance_cleared and clearance.academic_cleared:
                    program_stats[program_code]['fully_cleared'] += 1
                if clearance.finance_cleared:
                    program_stats[program_code]['finance_cleared'] += 1
                if clearance.academic_cleared:
                    program_stats[program_code]['academic_cleared'] += 1
                if not clearance.finance_cleared and not clearance.academic_cleared:
                    program_stats[program_code]['pending'] += 1
            except SemesterClearance.DoesNotExist:
                program_stats[program_code]['pending'] += 1
    
    # Convert to list for template
    program_stats_list = [
        {
            'code': code,
            **stats
        }
        for code, stats in program_stats.items()
    ]
    
    # Calculate totals
    totals = {
        'total_students': sum(s['total'] for s in program_stats.values()),
        'fully_cleared': sum(s['fully_cleared'] for s in program_stats.values()),
        'finance_cleared': sum(s['finance_cleared'] for s in program_stats.values()),
        'academic_cleared': sum(s['academic_cleared'] for s in program_stats.values()),
        'pending': sum(s['pending'] for s in program_stats.values()),
    }
    
    context = {
        'academic_year': academic_year,
        'semester': semester,
        'program_stats': program_stats_list,
        'totals': totals,
        'generated_date': date.today(),
        'generated_by': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'clearance_summary_report.html', context)


@login_required
#@permission_required('pass_book.view_semesterclearance', raise_exception=True)
def print_clearance_report(request, academic_year_id=None, semester_id=None):
    """
    Print a detailed clearance report for any academic year and semester.
    """
    # Get parameters - allow any academic year and semester
    academic_year = get_object_or_404(AcademicYear, pk=academic_year_id) if academic_year_id else None
    semester = get_object_or_404(Semester, pk=semester_id) if semester_id else None
    
    if not academic_year or not semester:
        # Use current active if not specified
        academic_year = AcademicYear.objects.filter(is_active=True).first()
        semester = Semester.objects.filter(is_active=True).first()
        
        if not academic_year or not semester:
            # If still no academic year or semester, use most recent
            academic_year = AcademicYear.objects.order_by('-start_date').first()
            semester = Semester.objects.order_by('-start_date').first()  # Changed from '-created_at' to '-start_date'
    
    if not academic_year or not semester:
        # Final fallback - empty report
        context = {
            'academic_year': None,
            'semester': None,
            'students_data': [],
            'generated_date': date.today(),
            'generated_by': request.user.get_full_name() or request.user.username,
        }
        return render(request, 'print_clearance_report.html', context)
    
    # Get all access numbers for the selected academic year and semester
    access_numbers = AccessNumber.objects.filter(
        academic_year=academic_year,
        semester=semester,
        is_active=True
    ).select_related(
        'student',
        'semester',
        'academic_year'
    ).prefetch_related(
        'semester_registration',
        'clearance'
    )
    
    # Get all clearance records for this semester
    clearance_records = SemesterClearance.objects.filter(
        access_number__in=access_numbers
    ).select_related('access_number__student')
    
    # Create a dictionary for quick lookup
    clearance_dict = {record.access_number_id: record for record in clearance_records}
    
    # Prepare student data with clearance status
    students_data = []
    
    for access_num in access_numbers:
        student = access_num.student
        clearance_record = clearance_dict.get(access_num.access_number)
        
        # Get semester registration
        semester_reg = getattr(access_num, 'semester_registration', None)
        
        # Build student data dictionary
        student_data = {
            'student': student,
            'access_number': access_num,
            'semester': semester,
            'academic_year': academic_year,
            'semester_registration': semester_reg,
            'clearance_record': clearance_record,
            'finance_cleared': clearance_record.finance_cleared if clearance_record else False,
            'academic_cleared': clearance_record.academic_cleared if clearance_record else False,
            'fully_cleared': clearance_record and clearance_record.finance_cleared and clearance_record.academic_cleared if clearance_record else False,
            'finance_clearance_date': clearance_record.finance_clearance_date if clearance_record else None,
            'academic_clearance_date': clearance_record.academic_clearance_date if clearance_record else None,
            'finance_officer_name': clearance_record.finance_officer_name if clearance_record else None,
            'academic_officer_name': clearance_record.academic_officer_name if clearance_record else None,
        }
        
        students_data.append(student_data)
    
    # Sort by student name
    students_data.sort(key=lambda x: x['student'].get_full_name() if hasattr(x['student'], 'get_full_name') else str(x['student']))
    
    # Calculate statistics
    total_students = len(students_data)
    fully_cleared = sum(1 for s in students_data if s['fully_cleared'])
    pending_clearance = total_students - fully_cleared
    
    context = {
        'academic_year': academic_year,
        'semester': semester,
        'students_data': students_data,
        'total_students': total_students,
        'fully_cleared': fully_cleared,
        'pending_clearance': pending_clearance,
        'generated_date': date.today(),
        'generated_by': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'print_clearance_report.html', context)


@login_required
#@permission_required('pass_book.view_semesterclearance', raise_exception=True)
def export_clearance_report_csv(request, academic_year_id=None, semester_id=None):
    """
    Export clearance report as CSV for any academic year and semester.
    """
    from django.http import HttpResponse
    import csv
    
    # Get parameters - allow any academic year and semester
    academic_year = get_object_or_404(AcademicYear, pk=academic_year_id) if academic_year_id else None
    semester = get_object_or_404(Semester, pk=semester_id) if semester_id else None
    
    if not academic_year or not semester:
        # Use current active if not specified
        academic_year = AcademicYear.objects.filter(is_active=True).first()
        semester = Semester.objects.filter(is_active=True).first()
        
        if not academic_year or not semester:
            # If still no academic year or semester, use most recent
            academic_year = AcademicYear.objects.order_by('-start_date').first()
            semester = Semester.objects.order_by('-start_date').first()  # Changed from '-created_at' to '-start_date'
    
    if not academic_year or not semester:
        # Return empty CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="clearance_report_{date.today().strftime("%Y%m%d")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['No data available'])
        return response
    
    # Get all access numbers for the selected academic year and semester
    access_numbers = AccessNumber.objects.filter(
        academic_year=academic_year,
        semester=semester,
        is_active=True
    ).select_related(
        'student',
        'semester',
        'academic_year'
    ).prefetch_related(
        'semester_registration',
        'clearance'
    )
    
    # Get all clearance records for this semester
    clearance_records = SemesterClearance.objects.filter(
        access_number__in=access_numbers
    ).select_related('access_number__student')
    
    # Create a dictionary for quick lookup
    clearance_dict = {record.access_number_id: record for record in clearance_records}
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="clearance_report_{academic_year}_{semester}_{date.today().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Student Name',
        'Access Number',
        'Program',
        'Session',
        'Finance Cleared',
        'Academic Cleared',
        'Fully Cleared',
        'Finance Clearance Date',
        'Academic Clearance Date',
        'Finance Officer',
        'Academic Officer',
        'Date Generated'
    ])
    
    # Write data rows
    for access_num in access_numbers:
        student = access_num.student
        clearance_record = clearance_dict.get(access_num.access_number)
        
        writer.writerow([
            student.get_full_name() if hasattr(student, 'get_full_name') else str(student),
            access_num.access_number,
            student.program.name if hasattr(student, 'program') and student.program else '',
            student.session,
            'Yes' if (clearance_record and clearance_record.finance_cleared) else 'No',
            'Yes' if (clearance_record and clearance_record.academic_cleared) else 'No',
            'Yes' if (clearance_record and clearance_record.finance_cleared and clearance_record.academic_cleared) else 'No',
            clearance_record.finance_clearance_date.strftime('%Y-%m-%d') if clearance_record and clearance_record.finance_clearance_date else '',
            clearance_record.academic_clearance_date.strftime('%Y-%m-%d') if clearance_record and clearance_record.academic_clearance_date else '',
            clearance_record.finance_officer_name if clearance_record and clearance_record.finance_officer_name else '',
            clearance_record.academic_officer_name if clearance_record and clearance_record.academic_officer_name else '',
            date.today().strftime('%Y-%m-%d')
        ])
    
    return response

class DeadSemesterApplicationsReportView(LoginRequiredMixin, ListView):
    """
    BUSINESS REPORT: Dead Semester Applications
    Used for: Registrar's office to track and manage applications.
    """
    model = DeadSemesterApplication
    template_name = 'student_registration/reports/dead_semester_applications_report.html'
    context_object_name = 'applications'
    paginate_by = 50
    def get_queryset(self):
        status_filter = self.request.GET.get('status')
        application_type_filter = self.request.GET.get('application_type')
        queryset = DeadSemesterApplication.objects.select_related('student__program').order_by('-application_date')
        if status_filter:
            if status_filter == 'APPROVED':
                queryset = queryset.filter(hod_recommended=True, faculty_recommended=True, registrar_recommended=True)
            elif status_filter == 'PENDING':
                queryset = queryset.filter(
                    Q(hod_recommended=False) | Q(faculty_recommended=False) | Q(registrar_recommended=False)
                )
        if application_type_filter:
            queryset = queryset.filter(application_type=application_type_filter)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['statuses'] = [('PENDING', 'Pending'), ('APPROVED', 'Approved')]
        context['application_types'] = DeadSemesterApplication._meta.get_field('application_type').choices
        context['report_title'] = "Dead Semester Applications Report"
        context['utc_now'] = timezone.now()  # This is timezone-aware
        return context