
# sms_attendance/urls.py
from django.urls import path
from .views import (
    LectureListView,          # For lecturers
    LectureCreateView,
    LectureDeleteView,
    take_attendance,
    AttendanceDashboardView,
    LectureAttendanceView,
    VerifyAttendanceView,
    StudentLectureListView,   # For students
    StudentAttendanceView,
    HomeView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    # Lecturer URLs
    path('lecturer/lectures/', LectureListView.as_view(), name='lecture-list'),
    path('lecturer/lectures/new/', LectureCreateView.as_view(), name='lecture-create'),
    path('lecturer/lectures/<int:pk>/delete/', LectureDeleteView.as_view(), name='lecture-delete'),
    path('lecturer/lectures/<int:pk>/attendance/', LectureAttendanceView.as_view(), name='lecture-attendance'),
    path('lecturer/attendance/<int:pk>/', take_attendance, name='take-attendance'),
    path('lecturer/dashboard/', AttendanceDashboardView.as_view(), name='dashboard'),
    
    # Student URLs
    path('student/lectures/', StudentLectureListView.as_view(), name='student-lecture-list'),
    path('student/verify/', VerifyAttendanceView.as_view(), name='verify-attendance'),
    path('student/my-attendance/', StudentAttendanceView.as_view(), name='student-attendance'),
]


