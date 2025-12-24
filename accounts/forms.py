
# accounts/forms.py


# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from pass_book.models import Program, Student  # For student registration

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control with-icon',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control with-icon',
            'placeholder': 'Password'
        })
    )


class StudentRegistrationForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Program"
    )
    nationality = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'})
    )
    student_contact = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student Contact'})
    )
    parent_guardian_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Parent/Guardian Name'})
    )
    parent_guardian_contact = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Parent/Guardian Contact'})
    )
    admission_year = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Admission Year (e.g., 2025)'})
    )
    session = forms.ChoiceField(
        choices=[('D', 'Day'), ('E', 'Evening'), ('W', 'Weekend')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        if commit:
            user.save()
            # Create linked Student profile
            Student.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                program=self.cleaned_data['program'],
                nationality=self.cleaned_data['nationality'],
                student_contact=self.cleaned_data['student_contact'],
                parent_guardian_name=self.cleaned_data['parent_guardian_name'],
                parent_guardian_contact=self.cleaned_data['parent_guardian_contact'],
                admission_year=self.cleaned_data['admission_year'],
                session=self.cleaned_data['session'],
            )
        return user


class StaffRegistrationForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    user_type = forms.ChoiceField(
        choices=[
            ('dean_of_students', 'Dean of Students'),
            ('finance_director', 'Finance Director'),
            ('academic_registrar', 'Academic Registrar'),
            ('head_of_department', 'Head of Department'),
            ('faculty_dean', 'Faculty Dean'),
            ('medical_officer', 'Medical Officer'),
            ('nche_officer', 'NCHE Officer'),
            ('lecturer', 'Lecturer'),
           # ('student','Student')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'user_type', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.cleaned_data['user_type']
        if commit:
            user.save()
        return user    


from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class StaffCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone_number", "user_type", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limit user_type choices to staff positions only
        STAFF_CHOICES = [
            ('dean_of_students', 'Dean of Students'),
            ('finance_director', 'Finance Director'),
            ('academic_registrar', 'Academic Registrar'),
            ('head_of_department', 'Head of Department'),
            ('faculty_dean', 'Faculty Dean'),
            ('medical_officer', 'Medical Officer'),
            ('nche_officer', 'NCHE Officer'),
            ('lecturer', 'Lecturer'),
           # ('student', 'Student')
        ]
        self.fields['user_type'].choices = STAFF_CHOICES

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Phone number already exists")
        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user