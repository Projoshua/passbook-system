
from django.views.generic import CreateView, DeleteView, ListView, DetailView, FormView 
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Lecture, Attendance
from django.views.generic import TemplateView
from django.utils import timezone
from .forms import LectureForm, AttendanceVerificationForm
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
import random
import string
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

##security considerations
from django.views.generic import TemplateView
#from django.contrib.auth.mixins import LoginRequiredMixin

class HomeView( TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data here
        return context




User = get_user_model()




# sms_attendance/views.py
class StudentLectureListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Lecture
    template_name = 'sms_attendance/student_lecture_list.html'
    
    def test_func(self):
        return self.request.user.is_student
    
    def get_queryset(self):
        return Lecture.objects.filter(
            end_time__gte=timezone.now() - timedelta(days=30)
        ).order_by('-start_time')







# sms_attendance/views.py
class StudentAttendanceView(LoginRequiredMixin, ListView):
    template_name = 'sms_attendance/student_attendance.html'
    context_object_name = 'attendance_records'
    
    def get_queryset(self):
        return Attendance.objects.filter(
            student=self.request.user
        ).select_related('lecture').order_by('-verification_time')


# sms_attendance/views.py
class StudentLectureListView(LoginRequiredMixin, ListView):
    model = Lecture
    template_name = 'sms_attendance/student_lecture_list.html'
    context_object_name = 'lectures'
    
    def get_queryset(self):
        return Lecture.objects.filter(
            end_time__gte=timezone.now() - timedelta(days=30)  # Last 30 days
        ).order_by('-start_time')
# sms_attendance/views.py



class VerifyAttendanceView(LoginRequiredMixin, FormView):
    template_name = 'sms_attendance/verify_attendance.html'
    form_class = AttendanceVerificationForm
    success_url = reverse_lazy('student-attendance')
    
    @method_decorator(ratelimit(key='user', rate='5/m', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def form_valid(self, form):
        # Only proceed if not rate limited (handled by decorator)
        code = form.cleaned_data['verification_code']
        try:
            attendance = Attendance.objects.get(
                student=self.request.user,
                verification_code=code,
                verified=False,
                lecture__start_time__lte=timezone.now(),
                lecture__end_time__gte=timezone.now()
            )
            attendance.verified = True
            attendance.save()
            messages.success(self.request, "Attendance verified successfully!")
        except Attendance.DoesNotExist:
            messages.error(self.request, "Invalid verification code or lecture not active")
        return super().form_valid(form)






class LectureAttendanceView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Lecture
    template_name = 'sms_attendance/lecture_attendance.html'
    context_object_name = 'lecture'
    
    def test_func(self):
        return self.request.user.is_lecturer
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Changed from course_unit to lecture
        context['attendance_records'] = Attendance.objects.filter(
            lecture=self.object
        ).select_related('student')
        return context







def take_attendance(request, pk):
    if not request.user.is_lecturer:
        messages.error(request, "Only lecturers can take attendance")
        return redirect('dashboard')
    
    lecture = get_object_or_404(Lecture, pk=pk, lecturer=request.user)
    
    if not lecture.is_active:
        messages.error(request, "This lecture is not currently active")
        return redirect('dashboard')
    
    verification_code = ''.join(random.choices(string.digits, k=6))
    students = User.objects.filter(user_type='student')
    
    for student in students:
        Attendance.objects.update_or_create(
            student=student,
            lecture=lecture,  # Changed from course_unit to lecture
            defaults={
                'verification_code': verification_code,
                'verified': False
            }
        )
    
    messages.success(request, f"Attendance started. Code: {verification_code}")
    return redirect('dashboard')

# sms_attendance/views.py
class AttendanceDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'sms_attendance/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_lecturer
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_lectures'] = Lecture.objects.filter(
            lecturer=self.request.user,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        )
        context['recent_lectures'] = Lecture.objects.filter(
            lecturer=self.request.user
        ).order_by('-start_time')[:5]
        return context
# For creating course units (lecturer only)
class LectureCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = LectureForm  # Only specify form_class, not fields
    template_name = 'sms_attendance/Lecture_form.html'
    success_url = reverse_lazy('lecture-list')
    
    def test_func(self):
        return self.request.user.is_lecturer
    
    def form_valid(self, form):
        form.instance.lecturer = self.request.user
        return super().form_valid(form)

# For listing course units (lecturer only)
class LectureListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Lecture
    template_name = 'sms_attendance/Lecture_list.html'
    
    def test_func(self):
        return self.request.user.is_lecturer
    
    def get_queryset(self):
        return Lecture.objects.filter(lecturer=self.request.user)

# For deleting course units (lecturer only)
class LectureDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Lecture
    template_name = 'sms_attendance/Lecture_confirm_delete.html'
    success_url = reverse_lazy('lecture_list')
    
    def test_func(self):
        return self.request.user == self.get_object().lecturer




class AttendanceDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'sms_attendance/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_lecturer
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_units'] = Lecture.objects.filter(
            lecturer=self.request.user,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        )
        return context



