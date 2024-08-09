from django.contrib.auth.models import AbstractUser, AbstractBaseUser
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver

class Users(AbstractUser):
    USER_TYPE_CHOICES = [
        ('customers', 'Customers'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    password = models.CharField(max_length=128)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='inactive')

    def __str__(self):
        return self.email
    
    def set_status_active(self):
        self.status = 'active'
        self.save()

    def set_status_inactive(self):
        self.status = 'inactive'
        self.save()

@receiver(user_logged_out)
def set_inactive_on_logout(sender, user, request, **kwargs):
    if user:
        user.set_status_inactive()

class Customers(models.Model):
    USER_TYPE_CHOICES = [
        ('customers', 'Customers'),
    ]
     
    customer_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name='customer_profile')
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES,default="customers")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    

class Moderator(models.Model):
    USER_TYPE_CHOICES = [
        ('moderator', 'Moderator'),
    ]
      
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    moderator_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE)
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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')


    def __str__(self):
        return self.email




class Bus(models.Model):
    bus_id = models.AutoField(primary_key=True)
    moderator_id = models.ForeignKey(Moderator, on_delete=models.CASCADE)
    bus_name = models.CharField(max_length=100)
    bus_number = models.CharField(max_length=20)
    bus_type = models.CharField(max_length=50)
    seating_capacity = models.IntegerField()
    departure_location = models.CharField(max_length=100)
    destination_location = models.CharField(max_length=100)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    date = models.DateField(null=False, blank=False)
    stops = models.TextField(blank=True, null=True)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    contact_number = models.CharField(max_length=20)
    email_address = models.EmailField()
    bus_image = models.ImageField(upload_to='media/', blank=True, null=True)
    driver_information = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('under_maintenance', 'Under Maintenance')])
    

    def __str__(self):
        return f'{self.bus_name} ({self.bus_number})'
    
    
class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    route_stops = models.TextField()  # More descriptive name for stops

    def __str__(self):
        return f"{self.source} to {self.destination}"

    def get_stops_list(self):
        return [stop.strip() for stop in self.route_stops.split(',') if stop.strip()]  # Using comma as separator

    def set_stops_list(self, stops_list):
        self.route_stops = ','.join(stops_list)  # Using comma as separator
