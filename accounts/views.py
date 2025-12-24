
# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .forms import LoginForm  # We'll create this next
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import LoginForm


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                
                # Redirect based on role
                if user.is_student:
                    # Check if student profile exists
                    if hasattr(user, 'student_profile') and user.student_profile:
                        # Redirect to their specific student details page
                        return redirect('pass_book:student_details', student_id=user.student_profile.id)
                    else:
                        # Student user exists but no profile linked
                        messages.warning(request, "Your student profile is not linked. Please contact administration.")
                        return redirect('pass_book:dashboard-passbook')
                else:
                    # Other user types go to dashboard
                    return redirect('pass_book:dashboard-passbook')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
    }
    if user.is_student:
        return render(request, 'accounts/dashboard_student.html', context)
    else:
        return render(request, 'accounts/dashboard_staff.html', context)



# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, StudentRegistrationForm, StaffRegistrationForm

# ... [keep your existing login, logout, dashboard views] ...

def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register_students.html', {'form': form})


def register_staff(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Staff account created for {username}!')
            return redirect('login')
    else:
        form = StaffRegistrationForm()

    return render(request, 'accounts/register_staff.html', {'form': form})



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import StaffCreationForm
from .models import User

def is_sysadmin(user):
    """Check if user is a sysadmin"""
    return user.is_authenticated and user.user_type == 'sysadmin'

@login_required
@user_passes_test(is_sysadmin)
def create_staff_view(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.created_by = request.user  # Track who created the staff
            user.save()
            messages.success(request, f'Staff member {user.get_full_name()} created successfully!')
            return redirect('staff_list')  # Redirect to staff list after creation
    else:
        form = StaffCreationForm()
    
    return render(request, 'accounts/create_staff.html', {'form': form})

@login_required
@user_passes_test(is_sysadmin)
def staff_list_view(request):
    """List all staff members"""
    staff_users = User.objects.filter(
        user_type__in=[
            'dean_of_students', 'finance_director', 'academic_registrar',
            'head_of_department', 'faculty_dean', 'medical_officer',
            'nche_officer', 'lecturer','student'
        ]
    ).order_by('-date_joined')
    
    paginator = Paginator(staff_users, 10)  # Show 10 staff per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'accounts/staff_list.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_sysadmin)
def delete_staff_view(request, user_id):
    """Delete a staff member"""
    if request.method == 'POST':
        try:
            staff_member = User.objects.get(id=user_id)
            staff_name = staff_member.get_full_name()
            staff_member.delete()
            messages.success(request, f'Staff member {staff_name} deleted successfully!')
        except User.DoesNotExist:
            messages.error(request, 'Staff member not found.')
        return redirect('staff_list')
    
    # If not POST, redirect to staff list
    return redirect('staff_list')

@login_required
@user_passes_test(is_sysadmin)
def edit_staff_view(request, user_id):
    """Edit staff member details"""
    try:
        staff_member = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Staff member not found.')
        return redirect('staff_list')
    
    if request.method == 'POST':
        # Update form fields
        staff_member.username = request.POST.get('username')
        staff_member.first_name = request.POST.get('first_name')
        staff_member.last_name = request.POST.get('last_name')
        staff_member.email = request.POST.get('email')
        staff_member.phone_number = request.POST.get('phone_number')
        staff_member.user_type = request.POST.get('user_type')
        
        # Validate unique constraints
        if User.objects.exclude(id=user_id).filter(email=staff_member.email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'accounts/edit_staff.html', {'staff_member': staff_member})
        
        if User.objects.exclude(id=user_id).filter(phone_number=staff_member.phone_number).exists():
            messages.error(request, 'Phone number already exists.')
            return render(request, 'accounts/edit_staff.html', {'staff_member': staff_member})
        
        staff_member.save()
        messages.success(request, f'Staff member {staff_member.get_full_name()} updated successfully!')
        return redirect('staff_list')
    
    # Show edit form
    return render(request, 'accounts/edit_staff.html', {'staff_member': staff_member})