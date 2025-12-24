
# sms_attendance/forms.py
from django import forms
from .models import Lecture
from django.contrib.admin.widgets import AdminSplitDateTime


class AttendanceVerificationForm(forms.Form):
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 6-digit code',
            'class': 'form-control'
        }),
        error_messages={
            'required': 'Please enter the verification code',
            'min_length': 'Code must be 6 digits'
        }
    )






class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = ['code', 'name', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert times to local timezone for display
        if self.instance.pk:
            self.initial['start_time'] = timezone.localtime(self.instance.start_time)
            self.initial['end_time'] = timezone.localtime(self.instance.end_time)



