from django.contrib.auth.models import AbstractUser, AbstractBaseUser
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import random
from decimal import Decimal

class Users(AbstractUser):
    USER_TYPE_CHOICES = [
        ('customers', 'Customers'),
        ('moderator', 'Moderator'),
        ('agent', 'Agent'),
        ('admin', 'Admin'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    LOGIN_STATUS_CHOICES = [
        ('enabled', 'Enabled'),
        ('disabled', 'Disabled'),
    ]
    
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    password = models.CharField(max_length=128)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='inactive')
    loginstatus = models.CharField(max_length=8, choices=LOGIN_STATUS_CHOICES, default='enabled')

    def __str__(self):
        return self.email
    
    def set_status_active(self):
        self.status = 'active'
        self.save()

    def set_status_inactive(self):
        self.status = 'inactive'
        self.save()

    def enable_login(self):
        self.loginstatus = 'enabled'
        self.save()

    def disable_login(self):
        self.loginstatus = 'disabled'
        self.save()

    def set_offline(self):
        self.status = 'inactive'
        self.save()

@receiver(user_logged_out)
def set_offline_on_logout(sender, user, request, **kwargs):
    if user:
        user.set_offline()

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
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)

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
    district = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='moderator_profiles/', blank=True, null=True)

    def __str__(self):
        return self.email

    def is_active_and_approved(self):
        return self.status == 'Approved' and self.user.is_active_user()




from django.utils import timezone

class Bus(models.Model):
    bus_id = models.AutoField(primary_key=True)
    moderator_id = models.ForeignKey(Moderator, on_delete=models.CASCADE)
    bus_name = models.CharField(max_length=100)
    bus_number = models.CharField(max_length=20, unique=True)
    bus_type = models.CharField(max_length=50)
    seating_capacity = models.IntegerField()
    departure_location = models.CharField(max_length=100)
    destination_location = models.CharField(max_length=100)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    date = models.DateField(null=False, blank=False)
    arrival_date = models.DateField(null=True, blank=True)
    stops = models.TextField(blank=True, null=True)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    bus_image = models.ImageField(upload_to='media/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('under_maintenance', 'Under Maintenance')])
    schedule_version = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return f'{self.bus_name} ({self.bus_number})'

    def get_feedback(self):
        return self.feedbacks.all()

    def average_rating(self):
        ratings = self.feedbacks.filter(rating__isnull=False).values_list('rating', flat=True)
        if ratings:
            return sum(ratings) / len(ratings)
        return 0

    def rating_distribution(self):
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        ratings = self.feedbacks.filter(rating__isnull=False).values_list('rating', flat=True)
        for rating in ratings:
            distribution[rating] += 1
        total = sum(distribution.values())
        return {k: (v / total) * 100 if total else 0 for k, v in distribution.items()}

    def get_recent_feedbacks(self, limit=2):
        return self.feedbacks.order_by('-created_at')[:limit]

    def get_liked_features(self):
        features = {}
        for feedback in self.feedbacks.all():
            if feedback.comment:
                words = feedback.comment.lower().split()
                for word in words:
                    if word in ['punctuality', 'driving', 'cleanliness', 'ac', 'staff', 'comfort']:
                        features[word] = features.get(word, 0) + 1
        return sorted(features.items(), key=lambda x: x[1], reverse=True)[:6]

    def should_be_under_maintenance(self):
        return self.arrival_date and timezone.now().date() > self.arrival_date

    def update_status(self):
        if self.should_be_under_maintenance():
            self.status = 'under_maintenance'
        else:
            self.status = 'active'

    def save(self, *args, **kwargs):
        self.update_status()
        super().save(*args, **kwargs)

    def increment_schedule_version(self):
        self.schedule_version += 1
        self.status = 'active'  # Set status to active when rescheduled
        super().save(update_fields=['schedule_version', 'status'])

    def can_reschedule(self):
        return self.arrival_date and self.arrival_date <= timezone.now().date()

class BusImage(models.Model):
    bus = models.ForeignKey(Bus, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='bus_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class DriversInfo(models.Model):
    driver_id = models.AutoField(primary_key=True)
    bus = models.OneToOneField(Bus, on_delete=models.CASCADE, related_name='driver_info')
    name = models.CharField(max_length=100)
    license = models.FileField(upload_to='driver_licenses/', validators=[FileExtensionValidator(['pdf'])])
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20)
    image = models.ImageField(upload_to='driver_images/')

    def __str__(self):
        return f"Driver for {self.bus.bus_name}"
    
    
class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=100)
    source_code = models.CharField(max_length=4, default='-')
    destination = models.CharField(max_length=100)
    destination_code = models.CharField(max_length=4, default='-')
    stops = models.TextField()

    def __str__(self):
        return f"{self.source} ({self.source_code}) to {self.destination} ({self.destination_code})"

    def get_stops_list(self):
        return [stop.strip() for stop in self.stops.split(',') if stop.strip()]

    def save(self, *args, **kwargs):
        self.source = self.source.strip()
        self.source_code = self.source_code.strip() or '-'
        self.destination = self.destination.strip()
        self.destination_code = self.destination_code.strip() or '-'
        self.stops = ','.join(stop.strip() for stop in self.stops.split(',') if stop.strip())
        super().save(*args, **kwargs)

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, AbstractBaseUser
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator
import random
from decimal import Decimal  # Add this import at the top of the file


class BusBooking(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
    ]
    booking_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='bookings')
    num_tickets = models.IntegerField()
    seat_booked = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    departure_location = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    booking_date = models.DateTimeField(default=timezone.now)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='Pending', null=True, blank=True)
    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    passenger_details = models.TextField(blank=True, null=True)
    schedule_version = models.IntegerField(default=1, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            super().save(*args, **kwargs)  # Save first to get the booking_id
            self.ticket_number = self.generate_ticket_number()
            self.save(update_fields=['ticket_number'])  # Save again to update ticket_number
        else:
            super().save(*args, **kwargs)

    def generate_ticket_number(self):
        serial = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        return f"TSA{serial}{self.booking_id:04d}"

    def __str__(self):
        return f'Booking {self.booking_id} for Customer {self.customer.email}'

    # @property
    # def departure_date(self):
    #     return self.bus.date  # This now correctly references the Bus model's date field

    def get_cancellation_deadline(self):
        # Assuming the Bus model has a 'date' and 'departure_time' field
        departure_datetime = timezone.make_aware(
            timezone.datetime.combine(self.bus.date, self.bus.departure_time)
        )
        return departure_datetime - timezone.timedelta(hours=24)

    def is_cancellable(self):
        return timezone.now() < self.get_cancellation_deadline()

    def calculate_refund_amount(self):
        return self.total_amount * Decimal('0.65')

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    payment_id = models.AutoField(primary_key=True)
    booking = models.ForeignKey(BusBooking, on_delete=models.CASCADE, related_name='payments')
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')  # ISO 4217 currency code
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50)  # e.g., 'card', 'upi', etc.
    payment_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Additional fields for card payments
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=20, blank=True, null=True)
    
    # Fields for potential refunds
    refund_id = models.CharField(max_length=255, blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    refund_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment {self.payment_id} for Booking {self.booking.booking_id}"

class Notification(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.message}"
    


class TravelReport(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    departure = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    travel_date = models.DateField()
    description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending', null=True, blank=True)

    def __str__(self):
        return f"{self.departure} to {self.destination} on {self.travel_date}"

class ReportPhoto(models.Model):
    report = models.ForeignKey(TravelReport, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='report_photos/')
    caption = models.CharField(max_length=255, blank=True)
    classification = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Photo for {self.report}"

from django.db import models
from django.conf import settings

class UserLocation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s location"

class SafetyNotification(models.Model):
    TYPES = (
        ('weather', 'Weather'),
        ('traffic', 'Traffic'),
    )
    type = models.CharField(max_length=10, choices=TYPES)
    message = models.TextField()
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class Agent(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    USER_TYPE_CHOICES = [
        ('agent', 'Agent'),
    ]

    agent_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name='agent_profile')
    moderator = models.ForeignKey(Moderator, on_delete=models.SET_NULL, null=True, related_name='agents')
    
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    mobile = models.CharField(max_length=20)
    
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    
    document = models.FileField(upload_to='agent_documents/', null=True, blank=True)
    
    profile_image = models.ImageField(upload_to='agent_profiles/', null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='agent')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"
    
class AgentJob(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),  # Add this status
    ]

    job_id = models.AutoField(primary_key=True)
    agent = models.ForeignKey('Agent', on_delete=models.CASCADE)
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE)
    selected_stop = models.CharField(max_length=255)
    date_assigned = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    original_arrival_date = models.DateTimeField(null=True, blank=True)  # Add this field

    def __str__(self):
        return f"Job {self.job_id} - Agent: {self.agent.first_name} {self.agent.last_name}, Stop: {self.selected_stop}, Status: {self.status}"

    def mark_as_completed(self):
        self.status = 'Completed'
        self.completed_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if not self.pk:  # If this is a new job
            self.original_arrival_date = self.bus.arrival_date
        super().save(*args, **kwargs)

class SafetyNotificationReport(models.Model):
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    report_id = models.AutoField(primary_key=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    report_title = models.CharField(max_length=255)
    incident_datetime = models.DateTimeField()
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    route = models.CharField(max_length=255)
    incident_type = models.CharField(max_length=100)
    severity_level = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, null=True, blank=True)
    stop = models.CharField(max_length=255, null=True, blank=True)
    affected_customers = models.ManyToManyField(Customers, related_name='safety_alerts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    schedule_version = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return f"Report {self.report_id} by {self.agent.first_name} {self.agent.last_name}"

    def save(self, *args, **kwargs):
        if self.bus and not self.schedule_version:
            self.schedule_version = self.bus.schedule_version
        super().save(*args, **kwargs)

class SafetyReportMedia(models.Model):
    report = models.ForeignKey(SafetyNotificationReport, related_name='media', on_delete=models.CASCADE)
    file = models.FileField(upload_to='safety_reports/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media for Report {self.report.report_id}"
    
class ChatMessage(models.Model):
    sender = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}: {self.content[:50]}"
    




from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Feedback(models.Model):
    RECOMMENDATION_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    booking = models.OneToOneField(BusBooking, on_delete=models.CASCADE, related_name='feedback')
    bus = models.ForeignKey('Bus', on_delete=models.SET_NULL, null=True, related_name='feedbacks')
    bus_name = models.CharField(max_length=255, null=True, blank=True)
    bus_route = models.CharField(max_length=255, null=True, blank=True)
    travel_date = models.DateField(null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    improvements = models.TextField(null=True, blank=True)
    recommend = models.CharField(max_length=3, choices=RECOMMENDATION_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Booking {self.booking.booking_id} - {self.bus_route or 'N/A'}"
    
class BusReschedule(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='reschedules')
    moderator = models.ForeignKey(Moderator, on_delete=models.SET_NULL, null=True, related_name='bus_reschedules')
    
    old_departure_location = models.CharField(max_length=100)
    old_destination_location = models.CharField(max_length=100)
    old_departure_date = models.DateField()
    old_departure_time = models.TimeField()
    old_arrival_date = models.DateField()
    old_arrival_time = models.TimeField()
    old_stops = models.TextField()
    old_ticket_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_departure_location = models.CharField(max_length=100)
    new_destination_location = models.CharField(max_length=100)
    new_departure_date = models.DateField()
    new_departure_time = models.TimeField()
    new_arrival_date = models.DateField()
    new_arrival_time = models.TimeField()
    new_stops = models.TextField()
    new_ticket_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rescheduled_at = models.DateTimeField(auto_now_add=True)
    
    # Add this field
    schedule_version = models.IntegerField(default=1, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.schedule_version:
            # Get the latest schedule version for this bus and increment it
            latest_reschedule = BusReschedule.objects.filter(bus=self.bus).order_by('-schedule_version').first()
            if latest_reschedule:
                self.schedule_version = latest_reschedule.schedule_version + 1
            else:
                self.schedule_version = self.bus.schedule_version + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reschedule for Bus {self.bus.bus_id} on {self.rescheduled_at}"