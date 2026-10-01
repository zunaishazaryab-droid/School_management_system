from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, UserProfileForm, CustomPasswordChangeForm
from apps.core.models import ActivityLog


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Session expiry based on remember_me
            remember_me = form.cleaned_data.get('remember_me')
            if not remember_me:
                request.session.set_expiry(0)  # Expires when browser closes
            else:
                request.session.set_expiry(1209600)  # 2 weeks
                
            # Log activity
            ActivityLog.log_activity(
                user=user,
                action='LOGIN',
                module='Accounts',
                description=f"User {user.username} logged in successfully.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if getattr(user, 'is_student', False) or getattr(user, 'is_parent', False):
                return redirect('students:student_dashboard')
            return redirect('core:dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.log_activity(
            user=request.user,
            action='LOGOUT',
            module='Accounts',
            description=f"User {request.user.username} logged out.",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        logout(request)
        messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user)
            password_form = CustomPasswordChangeForm(user)
            if profile_form.is_valid():
                profile_form.save()
                ActivityLog.log_activity(
                    user=user,
                    action='UPDATE',
                    module='Accounts',
                    description="User updated profile information.",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                messages.success(request, "Your profile has been updated successfully!")
                return redirect('accounts:profile')
            else:
                messages.error(request, "Please correct the errors in the profile form.")
                
        elif action == 'change_password':
            profile_form = UserProfileForm(instance=user)
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user_updated = password_form.save()
                update_session_auth_hash(request, user_updated)
                ActivityLog.log_activity(
                    user=user,
                    action='UPDATE',
                    module='Accounts',
                    description="User changed account password.",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                messages.success(request, "Your password was changed successfully!")
                return redirect('accounts:profile')
            else:
                messages.error(request, "Please correct the errors in the password form.")
        else:
            profile_form = UserProfileForm(instance=user)
            password_form = CustomPasswordChangeForm(user)
    else:
        profile_form = UserProfileForm(instance=user)
        password_form = CustomPasswordChangeForm(user)

    return render(request, 'accounts/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'user_obj': user
    })
