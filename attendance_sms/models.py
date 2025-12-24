
from django.db import models
from accounts.models import User
from django.utils import timezone

class Coursesubject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

class Lecture(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_lecturer': True})
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    @property
    def status(self):
        now = timezone.localtime(timezone.now())  # Convert to Uganda time
        start = timezone.localtime(self.start_time)
        end = timezone.localtime(self.end_time)
        
        if now < start:
            return "Upcoming"
        elif start <= now <= end:
            return "Active Now"
        else:
            return "Completed"
    
    @property
    def time_remaining(self):
        now = timezone.localtime(timezone.now())
        start = timezone.localtime(self.start_time)
        end = timezone.localtime(self.end_time)
        
        if now < start:
            delta = start - now
            hours, remainder = divmod(delta.seconds, 3600)
            minutes = remainder // 60
            return f"Starts in {hours}h {minutes}m"
        elif start <= now <= end:
            delta = end - now
            hours, remainder = divmod(delta.seconds, 3600)
            minutes = remainder // 60
            return f"Ends in {hours}h {minutes}m"
        else:
            return "Lecture completed"
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'})
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)  # Changed from course_unit
    verification_time = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    
    class Meta:
        unique_together = ('student', 'lecture')  # Updated from course_unit
    
    def __str__(self):
        return f"{self.student} - {self.lecture} - {'Verified' if self.verified else 'Pending'}"

class Enrollment(models.Model):
    student = models.ForeignKey(User, limit_choices_to={'user_type': 'student'}, on_delete=models.CASCADE)
    course_unit = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    date_enrolled = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'course_unit')



class AttendanceSettings(models.Model):
    course_unit = models.OneToOneField(Lecture, on_delete=models.CASCADE)
    allow_self_verification = models.BooleanField(default=True)
    verification_window_minutes = models.PositiveIntegerField(default=15)             


