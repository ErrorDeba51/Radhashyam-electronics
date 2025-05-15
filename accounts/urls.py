# radhashyam/accounts/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    SignupView,
    VerifyOTPView,
    LoginView,
    LogoutView,
    profile_view,
    ForgotPasswordView,
    CustomPasswordResetDoneView,
    CustomPasswordResetCompleteView,
    profile_edit,
    VerifyEmailChangeView
)

urlpatterns = [
    path('profile/', profile_view, name='profile'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),

    path('profile/edit/', profile_edit, name='profile_edit'),
    path('verify-email-change/', VerifyEmailChangeView.as_view(),
         name='verify_email_change'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ), name='password_reset_confirm'),

    path('reset/done/',
         CustomPasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('reset/complete/',
         CustomPasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
]
