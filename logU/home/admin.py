from django.contrib import admin
from .models import Users, Moderator, Customers, Bus, Location, BusBooking, Payment, TravelReport, ReportPhoto, Agent, AgentJob, SafetyNotificationReport, SafetyReportMedia, ChatMessage, DriversInfo, Feedback, BusReschedule

from django.utils.html import format_html

from django.contrib import admin
from .models import Customers
from django.utils.html import format_html

class CustomersAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'email', 'first_name', 'last_name', 'phone', 'address', 'city', 'district', 'postal_code', 'user_type', 'display_profile_picture')
    search_fields = ('email', 'first_name', 'last_name', 'city', 'district', 'postal_code')
    fields = ('email', 'first_name', 'last_name', 'phone', 'address', 'city', 'district', 'postal_code', 'user_type', 'profile_picture', 'display_profile_picture')
    readonly_fields = ('display_profile_picture',)
    
    def display_profile_picture(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50px" height="50px" style="border-radius: 50%;" />', obj.profile_picture.url)
        return "No picture"
    display_profile_picture.short_description = 'Profile Picture'


class ModeratorAdmin(admin.ModelAdmin):
    list_display = ('moderator_id', 'email', 'first_name', 'last_name', 'mobile', 'company', 'cv_file', 'city', 'gst', 'pan', 'pan_name', 'aadhar', 'user_type', 'status', 'profile_image', 'address', 'district')
    search_fields = ('moderator_id', 'email', 'first_name', 'last_name', 'company', 'city')

class UsersAdmin(admin.ModelAdmin):
    list_display = ('email','password', 'user_type', 'status', 'loginstatus')
    search_fields = ('email', 'user_type', 'status')

class BusAdmin(admin.ModelAdmin):
    list_display = ('bus_id', 'moderator_id', 'bus_name', 'bus_number', 'bus_type', 'seating_capacity', 'departure_location', 'destination_location', 'departure_time', 'arrival_time', 'date','arrival_date', 'status', 'ticket_price','schedule_version')
    search_fields = ('bus_name', 'bus_number', 'departure_location', 'destination_location')
#     inlines = [BusImageInline]

# class BusImageInline(admin.TabularInline):
#     model = BusImage
#     extra = 1

class LocationAdmin(admin.ModelAdmin):
    list_display = ('location_id', 'source', 'source_code', 'destination', 'destination_code', 'display_stops')
    search_fields = ('source', 'destination', 'source_code', 'destination_code')
    
    def display_stops(self, obj):
        return ", ".join(obj.get_stops_list())
    display_stops.short_description = 'Stops'

class BusBookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer', 'bus', 'num_tickets', 'seat_booked', 'total_amount', 'departure_location', 'destination', 'booking_date', 'payment_status', 'passenger_details','schedule_version')
    search_fields = ('booking_id', 'customer__email', 'bus__bus_name', 'departure_location', 'destination', 'payment_status')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'booking_id', 'customer_email', 'amount', 'currency', 'status', 'payment_method', 'payment_date')
    search_fields = ('payment_id', 'booking__booking_id', 'booking__customer__email', 'stripe_payment_intent_id')
    list_filter = ('status', 'payment_method', 'currency')

    def booking_id(self, obj):
        return obj.booking.booking_id
    booking_id.short_description = 'Booking ID'

    def customer_email(self, obj):
        return obj.booking.customer.email
    customer_email.short_description = 'Customer Email'

class ReportPhotoInline(admin.TabularInline):
    model = ReportPhoto
    extra = 1
    readonly_fields = ('display_image', 'image_link')

    def display_image(self, instance):
        if instance.image:
            return format_html('<img src="{}" width="100" height="100" />', instance.image.url)
        return "No image"

    def image_link(self, instance):
        if instance.image:
            return format_html('<a href="{}" target="_blank">{}</a>', instance.image.url, instance.image.name)
        return "No image"
    image_link.short_description = 'Image Path'

class TravelReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'departure', 'destination', 'travel_date', 'submitted_at', 'status', 'display_image_links')
    inlines = [ReportPhotoInline]
    
    def display_image_links(self, obj):
        links = []
        for photo in obj.photos.all():
            if photo.image:
                links.append(format_html('<a href="{}" target="_blank">{}</a>', photo.image.url, photo.image.name))
        return format_html(', '.join(links)) if links else "No images"
    display_image_links.short_description = 'Image Paths'

class SafetyReportMediaInline(admin.TabularInline):
    model = SafetyReportMedia
    extra = 1

class SafetyNotificationReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'agent', 'report_title', 'incident_datetime', 'location', 'incident_type', 'severity_level', 'status', 'bus', 'stop')
    list_filter = ('severity_level', 'status', 'incident_datetime')
    search_fields = ('report_title', 'agent__first_name', 'agent__last_name', 'location', 'incident_type')
    readonly_fields = ('submitted_at',)

    fieldsets = (
        ('Report Information', {
            'fields': ('agent', 'report_title', 'incident_datetime', 'location', 'latitude', 'longitude', 'route')
        }),
        ('Incident Details', {
            'fields': ('incident_type', 'severity_level', 'description')
        }),
        ('Status', {
            'fields': ('status', 'submitted_at')
        }),
    )

    inlines = [SafetyReportMediaInline]

class AgentAdmin(admin.ModelAdmin):
    list_display = ('agent_id', 'email', 'first_name', 'last_name', 'mobile', 'company', 'document', 'location', 'moderator', 'user_type', 'status', 'profile_image', 'address', 'city', 'district')
    search_fields = ('agent_id', 'email', 'first_name', 'last_name', 'company', 'location')
    list_filter = ('status', 'user_type')

    def document(self, obj):
        if obj.document:
            return format_html('<a href="{}" target="_blank">View Document</a>', obj.document.url)
        return "No document"
    document.short_description = 'Document'

class AgentJobAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'agent', 'bus', 'selected_stop', 'date_assigned', 'status', 'original_arrival_date','completed_at')
    list_filter = ('status', 'date_assigned')
    search_fields = ('agent__first_name', 'agent__last_name', 'bus__bus_name', 'selected_stop')
    readonly_fields = ('date_assigned',)

    def agent_name(self, obj):
        return f"{obj.agent.first_name} {obj.agent.last_name}"
    agent_name.short_description = 'Agent Name'


class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'content', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('sender__username', 'recipient__username', 'content')


class DriversInfoAdmin(admin.ModelAdmin):
    list_display = ['driver_id', 'name', 'email', 'contact_number', 'bus']
    search_fields = ('name', 'email', 'contact_number', 'bus__bus_name')

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('booking', 'bus', 'bus_name', 'bus_route', 'travel_date', 'rating', 'recommend', 'created_at')
    list_filter = ('rating', 'recommend', 'travel_date')
    search_fields = ('bus_name', 'bus_route', 'comment')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking', 'bus', 'bus_name', 'bus_route', 'travel_date')
        }),
        ('Feedback Details', {
            'fields': ('rating', 'comment', 'improvements', 'recommend')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('booking', 'bus', 'bus_name', 'bus_route', 'travel_date')
        return self.readonly_fields

class BusRescheduleAdmin(admin.ModelAdmin):
    list_display = ('bus', 'moderator', 'old_departure_location', 'old_destination_location', 'old_departure_date', 'old_departure_time', 'old_arrival_date', 'old_arrival_time', 'old_stops', 'old_ticket_price', 'new_departure_location', 'new_destination_location', 'new_departure_date', 'new_departure_time', 'new_arrival_date', 'new_arrival_time', 'new_stops', 'new_ticket_price', 'rescheduled_at')
    search_fields = ('bus__bus_name', 'moderator__first_name', 'old_departure_location', 'old_destination_location')
    list_filter = ('rescheduled_at',)
    readonly_fields = ('rescheduled_at',)

admin.site.register(Customers, CustomersAdmin)
admin.site.register(Moderator, ModeratorAdmin)
admin.site.register(Users, UsersAdmin)
admin.site.register(Bus, BusAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(BusBooking, BusBookingAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(TravelReport, TravelReportAdmin)
admin.site.register(Agent, AgentAdmin)
admin.site.register(AgentJob, AgentJobAdmin)
admin.site.register(SafetyNotificationReport, SafetyNotificationReportAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(DriversInfo, DriversInfoAdmin)
admin.site.register(ReportPhoto)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(BusReschedule, BusRescheduleAdmin)