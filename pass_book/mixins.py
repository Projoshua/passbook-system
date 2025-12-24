# pass_book/mixins.py (or wherever you prefer to place utility classes)
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class SysAdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure the user is a sysadmin.
    Can be used for views requiring sysadmin access.
    """
    def test_func(self):
        user = self.request.user
        # Check if the user is authenticated and is a sysadmin
        return user.is_authenticated and user.is_sysadmin

    def handle_no_permission(self):
        # You can customize the behavior here
        # Option 1: Raise PermissionDenied (default behavior)
        raise PermissionDenied("You do not have permission to access this resource.")

        # Option 2: Redirect to a specific page (uncomment if preferred)
        # from django.shortcuts import redirect
        # from django.contrib import messages
        # messages.error(self.request, "You must be a System Administrator to access this page.")
        # return redirect('login') # Or another appropriate URL