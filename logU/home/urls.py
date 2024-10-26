from django.urls import path,include
from .views import views
from django.contrib.auth import views as auth_views 
from .views import add_bus
from django.conf import settings
from django.conf.urls.static import static
from .models import BusBooking  # Assuming you have a Booking model
from home.views import views2, views3

urlpatterns = [
   
    path('booking-confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('save-passenger-details/<int:booking_id>/', views.save_passenger_details, name='save_passenger_details'),
    path('', views.index, name="index"),
    path('signup', views.signup, name="signup"),
    path('login', views.loginn, name="login"),
    path('welcome/', views.welcomePage, name="welcome"),
    path('profile/', views.profile, name='profile'),
    path('booking/', views.booking, name='booking'),
    path('admin1/', views.admin1, name='admin1'),
    path('mod_reg/', views.mod_reg, name='mod_reg'),  
    path('signup_moderator/', views.signup_moderator, name='signup_moderator'),
    path('mod_profile/', views.mod_profile, name='mod_profile'),
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
    path('buses_added_by_moderator/', views.buses_added_by_moderator, name='buses_added_by_moderator'),
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
    path('create-booking/', views.create_booking, name='create_booking'),
    path('check-temporary-booking/', views.check_temporary_booking, name='check_temporary_booking'),
    path('cancel-temporary-booking/', views.cancel_temporary_booking, name='cancel_temporary_booking'),
    path('create-checkout-session/', views.CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('booking-success/', views.booking_success, name='booking_success'),
    path('booking-cancel/', views.booking_cancel, name='booking_cancel'),
    path('your_bookings/', views.your_bookings, name='your_bookings'),
    path('e_ticket/', views.e_ticket, name='e_ticket'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('api/bus-availability/<int:bus_id>/', views.bus_availability, name='bus_availability'),
    path('api/booked-seats/<int:bus_id>/', views.get_booked_seats, name='get_booked_seats'),
    path('get-notifications/', views.get_notifications, name='get_notifications'),
    path('agent_registration/', views.agent_registration, name='agent_registration'),
    path('get_moderator_details/', views.get_moderator_details, name='get_moderator_details'),
    path('register_agent/', views.register_agent, name='register_agent'),
    path('agent_request/', views.agent_requests, name='agent_requests'),
    path('agent_welcome/', views.agent_welcome, name='agent_welcome'),  # Add this line
    path('get-safety-alerts/', views.get_safety_alerts, name='get_safety_alerts'),
    path('api/all-bus-reviews/<int:bus_id>/', views.all_bus_reviews, name='all_bus_reviews'),
    path('api/bus-images/<int:bus_id>/', views.bus_images, name='bus_images'),
    path('get_buses_with_stops/', views.get_buses_with_stops, name='get_buses_with_stops'),
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




    #views2
    path('weather-forecast/', views2.weather_forecast, name='weather_forecast'),
    path('update-location/', views2.update_location, name='update_location'),
    path('get-safety-notifications/', views2.get_safety_notifications, name='get_safety_notifications'),
    path('test-weather-api/', views2.test_weather_api, name='test_weather_api'),
    # path('safety-notifications/', views2.safety_notifications_page, name='safety_notifications_page'),
    path('get_weather_data/', views2.get_weather_data, name='get_weather_data'),
    path('mod_agentlist/', views2.mod_agentlist, name='mod_agentlist'),
    path('mod_agentdetails/<int:agent_id>/', views2.mod_agentdetails, name='mod_agentdetails'),
    path('mod_agent_previous_jobs/<int:agent_id>/', views2.mod_agent_previous_jobs, name='mod_agent_previous_jobs'),
    path('complete_job/', views2.complete_job, name='complete_job'),
    path('save_agent_job/', views2.save_agent_job, name='save_agent_job'),
    path('process_job_request/', views2.process_job_request, name='process_job_request'),
    path('moderator_job_requests/', views2.moderator_job_requests, name='moderator_job_requests'),
    path('safety_notification_report/', views2.safety_notification_report, name='safety_notification_report'),
    path('notifications_report/', views2.notifications_report, name='notifications_report'),
    path('view_notification_report/<int:report_id>/', views2.view_notification_report, name='view_notification_report'),
    path('toggle-bus-status/<int:bus_id>/', views2.toggle_bus_status, name='toggle_bus_status'),
    path('process_report/', views2.process_report, name='process_report'),
    path('debug_notification/<int:report_id>/', views2.debug_notification, name='debug_notification'),
    path('agent_view_reports/', views2.agent_view_reports, name='agent_view_reports'),
    path('send-chat-message/', views2.send_chat_message, name='send_chat_message'),
    path('get-chat-messages/', views2.get_chat_messages, name='get_chat_messages'),
    path('get-chat-users/', views2.get_chat_users, name='get_chat_users'),
    path('get_new_messages/', views2.get_new_messages, name='get_new_messages'),
    path('agent_profile_update/', views2.agent_profile_update, name='agent_profile_update'),
    path('check_email/', views2.check_email, name='check_email'),
    path('check_current_job/', views2.check_current_job, name='check_current_job'),


    #views3
    path('toggle-moderator-status/<int:moderator_id>/', views3.toggle_moderator_status, name='toggle_moderator_status'),
    path('toggle_customer_status/<int:customer_id>/', views3.toggle_customer_status, name='toggle_customer_status'),
    path('agent_details/', views3.agent_details, name='agent_details'),
    path('toggle_agent_status/<int:agent_id>/', views3.toggle_agent_status, name='toggle_agent_status'),
    path('bus_details/', views3.bus_details, name='bus_details'),
    path('view_details/<int:bus_id>/', views3.view_details, name='view_details'),
    path('submit-travel-report/', views3.submit_travel_report, name='submit_travel_report'),
    path('view_reports/', views3.view_reports, name='view_reports'),
    path('report-detail/<int:report_id>/', views3.report_detail, name='report_detail'),
    path('submit-feedback/', views3.submit_feedback, name='submit_feedback'),       
    path('view-feedback/', views3.view_feedback, name='view_feedback'),
    path('view-bus-bookings/', views3.view_bus_bookings, name='view_bus_bookings'),
    path('get_bus_bookings/<int:bus_id>/', views3.get_bus_bookings, name='get_bus_bookings'),
    path('admin_add_news/', views3.admin_add_news, name='admin_add_news'),
    path('approve_report/<int:report_id>/', views3.approve_report, name='approve_report'),
    path('reject_report/<int:report_id>/', views3.reject_report, name='reject_report'),
    path('blogs/', views3.blogs, name='blogs'),
    path('blog-detail/<int:report_id>/', views3.blog_detail, name='blog_detail'),
    path('get_available_routes/', views3.get_available_routes, name='get_available_routes'),
    path('booking_cancellation/', views3.booking_cancellation, name='booking_cancellation'),
    path('cancel_booking/<int:booking_id>/', views3.cancel_booking, name='cancel_booking'),
    path('reschedule_bus/', views3.reschedule_bus, name='reschedule_bus'),
    path('api/bus-images/<int:bus_id>/', views3.bus_images, name='bus_images'),  
    path('get_bus_schedules/<int:bus_id>/', views3.get_bus_schedules, name='get_bus_schedules'),
    path('admin_bus_bookings/', views3.admin_bus_bookings, name='admin_bus_bookings'),
    path('admin_get_moderator_buses/<int:moderator_id>/', views3.admin_get_moderator_buses, name='admin_get_moderator_buses'),
    path('admin_get_bus_schedules/<int:bus_id>/', views3.admin_get_bus_schedules, name='admin_get_bus_schedules'),
    path('admin_get_bus_bookings/<int:bus_id>/<int:schedule_version>/', views3.admin_get_bus_bookings, name='admin_get_bus_bookings'),
    path('admin_download_bookings_pdf/<int:bus_id>/<int:schedule_version>/', views3.admin_download_bookings_pdf, name='admin_download_bookings_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
