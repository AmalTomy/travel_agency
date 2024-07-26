from django.contrib import admin
from .models import Users, Moderator, Customers

class CustomersAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone', 'address', 'user_type')
    search_fields = ('email', 'first_name', 'last_name')

class ModeratorAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'mobile', 'company', 'cv_file', 'city', 'gst', 'pan', 'pan_name', 'aadhar', 'user_type')
    search_fields = ('email', 'first_name', 'last_name', 'company', 'city')

class UsersAdmin(admin.ModelAdmin):
    list_display = ('email','password', 'user_type')
    search_fields = ('email', 'user_type')

admin.site.register(Customers, CustomersAdmin)
admin.site.register(Moderator, ModeratorAdmin)
admin.site.register(Users, UsersAdmin)
