from django.contrib import admin
from .models import Users, Moderator, Customers
from .models import Bus
from django.utils.html import format_html


class CustomersAdmin(admin.ModelAdmin):
    list_display = ('customer_id','email', 'first_name', 'last_name', 'phone', 'address', 'user_type', 'display_profile_picture')
    search_fields = ('email', 'first_name', 'last_name')
    fields = ('email', 'first_name', 'last_name', 'phone', 'address', 'user_type', 'profile_picture', 'display_profile_picture' )
    readonly_fields = ('display_profile_picture',)
    
    def display_profile_picture(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50px" height="50px" style="border-radius: 50%;" />', obj.profile_picture.url)
        return "No picture"
    display_profile_picture.short_description = 'Profile Picture'

class ModeratorAdmin(admin.ModelAdmin):
    list_display = ('moderator_id', 'email', 'first_name', 'last_name', 'mobile', 'company', 'cv_file', 'city', 'gst', 'pan', 'pan_name', 'aadhar', 'user_type', 'status')
    search_fields = ('moderator_id', 'email', 'first_name', 'last_name', 'company', 'city')

class UsersAdmin(admin.ModelAdmin):
    list_display = ('email','password', 'user_type', 'status')
    search_fields = ('email', 'user_type', 'status')

class BusAdmin(admin.ModelAdmin):
    list_display = ('bus_id', 'moderator_id', 'bus_name', 'bus_number', 'bus_type', 'seating_capacity', 'departure_location', 'destination_location', 'departure_time', 'arrival_time', 'date','status')
    search_fields = ('bus_name', 'bus_number', 'departure_location', 'destination_location')
   
    
admin.site.register(Customers, CustomersAdmin)
admin.site.register(Moderator, ModeratorAdmin)
admin.site.register(Users, UsersAdmin)
admin.site.register(Bus, BusAdmin)
