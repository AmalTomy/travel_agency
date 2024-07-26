from django.contrib.auth.models import AbstractUser, AbstractBaseUser
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password

class Users(AbstractUser):
    USER_TYPE_CHOICES = [
        ('customers', 'Customers'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    password = models.CharField(max_length=128)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    def __str__(self):
        return self.email
    
class Customers(models.Model):
    USER_TYPE_CHOICES = [
        ('customers', 'Customers'),
    ]

    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES,default="customers")

    def __str__(self):
        return self.email
    

class Moderator(models.Model):
    USER_TYPE_CHOICES = [
        ('moderator', 'Moderator'),
    ]
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    password = models.CharField(max_length=128)
    cv_file = models.FileField(upload_to='media/', null=True, blank=True)  # Use media directory
    gst = models.CharField(max_length=15, null=True, blank=True)
    pan = models.CharField(max_length=10, null=True, blank=True)
    pan_name = models.CharField(max_length=100, null=True, blank=True)
    aadhar = models.CharField(max_length=12, null=True, blank=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    def __str__(self):
        return self.email



