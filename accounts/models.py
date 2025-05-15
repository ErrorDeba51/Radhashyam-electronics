# radhashyam/accounts/models.py
from django.db import IntegrityError
from cart.models import Cart
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email).lower().strip()
        if UserProfile.objects.filter(email=email).exists():
            raise IntegrityError("Email already exists")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and saves a superuser with the given email and password
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


class UserProfile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)

    # Required fields
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the full name of the user if available, otherwise return email"""
        return self.full_name if self.full_name else self.email.split('@')[0]

    def get_short_name(self):
        """Return the short name for the user (first part of email)"""
        return self.email.split('@')[0]

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


@receiver(post_save, sender=UserProfile)
def create_user_cart(sender, instance, created, **kwargs):
    """Automatically create a cart for new users"""
    if created:
        Cart.objects.create(user=instance)


@receiver(post_save, sender=UserProfile)
def save_user_cart(sender, instance, **kwargs):
    """Save the cart when user is saved"""
    instance.cart.save()
