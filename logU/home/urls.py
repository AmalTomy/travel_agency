from django.urls import path,include
from . import views
from django.contrib.auth import views as auth_views 
from .views import add_bus
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name="index"),
    path('signup', views.signup, name="signup"),
    path('login', views.loginn, name="login"),
    path('welcome', views.welcomePage, name="welcome"),
    path('profile/', views.profile, name='profile'),
    path('booking/', views.booking, name='booking'),
    path('admin1/', views.admin1, name='admin1'),
    path('mod_reg/', views.mod_reg, name='mod_reg'),  
    path('signup_moderator/', views.signup_moderator, name='signup_moderator'),
    path('mod_sch/', views.mod_sch, name='mod_sch'),
    path('mod_home/', views.mod_home, name='mod_home'),
    path('customer_details/', views.customer_details, name='customer_details'),
    path('moderator_details/', views.moderator_details, name='moderator_details'),
    path('add_bus/', views.add_bus, name='add_bus'),
    path('profile/', views.profile, name='profile'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('booking/', views.booking_page, name='booking_page'),
    path('check_email/', views.check_email, name='check_email'),
    path('pending-registration/', views.pending_registration, name='pending_registration'),
    path('mod_req_details/', views.mod_req_details, name='mod_req_details'),
    path('buses-added/', views.buses_added_by_moderator, name='buses_added_by_moderator'),
    path('edit-bus/<int:bus_id>/', views.edit_bus, name='edit_bus'),
    path('delete-bus/<int:bus_id>/', views.delete_bus, name='delete_bus'),
    path('bus-list/', views.bus_list, name='bus_list'),
    path('logout/', views.signout, name='signout'),
    path('ajax/check_email/', views.check_email, name='check_email'),
    path('deactivate-moderator/<int:moderator_id>/', views.deactivate_moderator, name='deactivate_moderator'),
    path('deactivate-customer/<int:customer_id>/', views.deactivate_customer, name='deactivate_customer'),
    path('check_email/', views.check_email, name='check_email'),
    path('add_locations/', views.add_locations, name='add_locations'),
    path('upload_excel/', views.upload_excel, name='upload_excel'),
    path('get_locations/', views.get_locations, name='get_locations'),
    path('get_stops/', views.get_stops, name='get_stops'),
    path('check-email/', views.check_email, name='check_email'),




    
    
   path('password_reset/',auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html'),name="password_reset"),
    path('password_reset_done/',auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_sent.html'
    ),name="password_reset_done"),
    path('password_reset_confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ),name="password_reset_confirm"),
    path('password_reset_complete/',auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ),name="password_reset_complete"),
    
    path('accounts/', include('allauth.urls')),
    path('ajax/check_email/', views.check_email, name='check_email'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)