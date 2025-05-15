# radhashyam/accounts/views.py

import re
import random
from django.shortcuts import render, redirect
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetCompleteView
)
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.views import View
from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.cache import cache
from django.urls import reverse, reverse_lazy
from django.conf import settings
from django.db import IntegrityError, transaction
from .models import UserProfile


@login_required
def profile_view(request):
    user = request.user
    context = {
        'user': user,
        'phone': user.phone
    }
    return render(request, 'accounts/profile.html', context)


class OTPMixin:
    @staticmethod
    def generate_and_send_otp(email):
        otp = random.randint(100000, 999999)
        cache.set(f'otp_{email}', otp, timeout=600)
        print(f"DEBUG: OTP {otp} stored for {email}")
        send_mail(
            'Your OTP Verification',
            f'Your OTP is: {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return otp


@login_required
def profile_edit(request):
    if request.method == 'POST':
        user = request.user
        new_email = request.POST.get('email', '').lower()

        if new_email != user.email:
            otp = random.randint(100000, 999999)
            cache.set(f'email_change_{new_email}', otp, 600)

            send_mail(
                'Verify Email Change',
                f'Your OTP for email change: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [new_email]
            )

            request.session['pending_email'] = new_email
            return redirect('verify_email_change')

        user.full_name = request.POST.get('name', user.full_name)
        user.phone = request.POST.get('phone', user.phone)
        user.save(update_fields=['full_name', 'phone'])
        return redirect('profile')

    return render(request, 'accounts/profile_edit.html')


class VerifyEmailChangeView(View):
    def get(self, request):
        return render(request, 'accounts/verify_email_change.html')

    def post(self, request):
        user = request.user
        otp = request.POST.get('otp')
        new_email = request.session.get('pending_email')

        cached_otp = cache.get(f'email_change_{new_email}')

        if str(otp) == str(cached_otp):
            user.email = new_email
            user.save()
            cache.delete(f'email_change_{new_email}')
            del request.session['pending_email']
            return redirect('profile')

        return render(request, 'accounts/verify_email_change.html',
                      {'error': 'Invalid OTP'})


class SignupView(OTPMixin, View):
    def get(self, request):
        if 'reg_data' in request.session:
            email = request.session['reg_data'].get('email')
            if email:
                cache.delete(f'otp_{email}')
                cache.delete(f'email_change_{email}')
            del request.session['reg_data']
            request.session.modified = True
        return render(request, 'accounts/signup.html')

    def post(self, request):
        email = request.POST.get('email', '').lower().strip()
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        password = request.POST.get('password', '')

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return JsonResponse({'error': 'Invalid email format'}, status=400)

        if UserProfile.objects.filter(email__iexact=email).exists():
            return JsonResponse({'error': 'Email already registered'}, status=400)

        request.session['reg_data'] = {
            'email': email,
            'name': name,
            'phone': phone,
            'pincode': pincode,
            'password': password
        }
        request.session.modified = True

        try:
            self.generate_and_send_otp(email)
            return JsonResponse({'message': 'OTP sent successfully'})
        except Exception as e:
            return JsonResponse({'error': f'Failed to send OTP: {str(e)}'}, status=500)


class VerifyOTPView(View):
    @transaction.atomic
    def post(self, request):
        email = request.POST.get('email', '').lower().strip()
        otp_entered = request.POST.get('otp', '')
        reg_data = request.session.get('reg_data')

        if otp_entered.lower() == 'resend':
            if reg_data and reg_data.get('email', '').lower() == email:
                SignupView.generate_and_send_otp(email)
                return JsonResponse({'message': 'OTP sent successfully'})
            return JsonResponse({'error': 'Session expired'}, status=400)

        if not reg_data or reg_data.get('email', '').lower() != email:
            if 'reg_data' in request.session:
                del request.session['reg_data']
            return JsonResponse({'error': 'Session expired'}, status=400)

        try:
            otp_entered = int(otp_entered)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid OTP format'}, status=400)

        cache_key = f'otp_{email}'
        otp_cached = cache.get(cache_key)

        if not otp_cached:
            if reg_data and reg_data.get('email', '').lower() == email:
                SignupView.generate_and_send_otp(email)
                return JsonResponse({
                    'error': 'OTP expired. New OTP sent automatically.',
                    'resend': True
                }, status=400)
            return JsonResponse({'error': 'OTP expired. Please restart registration.'}, status=400)

        if int(otp_entered) == int(otp_cached):
            try:

                if UserProfile.objects.filter(email__iexact=email).exists():
                    return JsonResponse({'error': 'Email taken'}, status=400)

                user = UserProfile.objects.create_user(
                    email=email,
                    full_name=reg_data['name'],
                    password=reg_data['password'],
                    phone=reg_data['phone'],
                    pincode=reg_data['pincode'],
                    is_active=True
                )
                login(request, user)
                request.session.cycle_key()
                del request.session['reg_data']
                cache.delete(cache_key)
                return JsonResponse({'success': True, 'redirect': reverse('home')})
            except IntegrityError as e:
                return JsonResponse({
                    'error': 'This email is already registered. Please login.'
                }, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Account creation failed: {str(e)}'}, status=500)

        return JsonResponse({'error': 'Invalid OTP'}, status=400)


class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        form.cleaned_data['username'] = form.cleaned_data['username'].lower()
        response = super().form_valid(form)
        self.request.session.cycle_key()

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect': self.get_success_url()
            })
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Invalid credentials',
                'errors': form.errors.get_json_data()
            }, status=401)
        return super().form_invalid(form)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('home')


class ForgotPasswordView(PasswordResetView):
    template_name = 'accounts/forgot_password.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'
