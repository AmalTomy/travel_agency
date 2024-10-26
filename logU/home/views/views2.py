import numpy as np
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from home.models import (
       UserLocation, SafetyNotificationReport, TravelReport, ReportPhoto, Agent,
       Moderator, Bus, SafetyReportMedia, ChatMessage, Users, Customers, BusBooking,
       AgentJob, Location, Notification, Payment, SafetyNotificationReport
   )
from datetime import datetime
from home.utils import send_notification as send_safety_notification
import pytz
from home.utils import get_users_in_area
from home.api_clients import WeatherAPI, TrafficAPI
import requests
import json
import traceback
import logging
import os


API_KEY = "45b01a7f6a9893cc9370a6fd91f105fb"


def get_mumbai_time():
    mumbai_tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(mumbai_tz)



def weather_forecast(request):
    context = {}
    city = request.GET.get('city')
    if city:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={settings.OPENWEATHERMAP_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            current_weather = data["list"][0]

            # Get the current date in Mumbai (or any timezone you prefer)
            mumbai_tz = pytz.timezone('Asia/Kolkata')
            current_date = datetime.now(mumbai_tz).date()

            context = {
                "city_name": data["city"]["name"],
                "city_country": data["city"]["country"],
                "temp": round(current_weather["main"]["temp"] - 273.15),
                "description": current_weather["weather"][0]["description"],
                "icon": current_weather["weather"][0]["icon"],
                "current_date": current_date,
                "temp_max": round(current_weather["main"]["temp_max"] - 273.15),
                "temp_min": round(current_weather["main"]["temp_min"] - 273.15),
                "humidity": current_weather["main"]["humidity"],
                "precipitation": current_weather.get("pop", 0) * 100,
                "wind": current_weather["wind"]["speed"],
                "daily_forecast": data["list"][::8],
            }
            
            # Prepare data for the chart
            chart_labels = [forecast["dt_txt"] for forecast in data["list"][:8]]
            context["chart_labels"] = json.dumps([dt.split()[1][:5] for dt in chart_labels])
            context["chart_data"] = json.dumps([round(forecast["main"]["temp"] - 273.15, 1) for forecast in data["list"][:8]])
            
        else:
            context["error"] = "City not found. Please check the spelling."
    
    return render(request, "weather_forecast.html", context)


@login_required
@require_POST
def update_location(request):
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)
        
        UserLocation.objects.update_or_create(
            user=request.user,
            defaults={'latitude': latitude, 'longitude': longitude}
        )
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.exception(f"Error in update_location: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

logger = logging.getLogger(__name__)



def get_traffic_data(lat, lng):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={lat},{lng}&destination={lat},{lng}&mode=driving&key={settings.GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        route = data['routes'][0]
        if 'warnings' in route:
            return route['warnings']
    return []




@login_required
def get_safety_notifications(request):
    try:
        user_location = UserLocation.objects.get(user=request.user)
        
        weather_api = WeatherAPI()
        
        weather_alerts = weather_api.get_alerts(user_location.latitude, user_location.longitude)
        traffic_incidents = get_traffic_data(user_location.latitude, user_location.longitude)
        
        notifications = []
        for alert in weather_alerts:
            notifications.append({
                'type': 'weather',
                'message': alert.get('event', 'Unknown weather event'),
            })
        
        for incident in traffic_incidents:
            notifications.append({
                'type': 'traffic',
                'message': incident,
            })
        
        return JsonResponse({'notifications': notifications})
    except UserLocation.DoesNotExist:
        logger.error(f"User location not set for user {request.user.id}")
        return JsonResponse({'notifications': [], 'message': 'User location not set. Please update your location.'})
    except Exception as e:
        error_message = f"Error in get_safety_notifications: {str(e)}"
        error_traceback = traceback.format_exc()
        logger.error(f"{error_message}\n{error_traceback}")
        return JsonResponse({'error': 'Internal server error', 'details': error_message}, status=500)


def test_weather_api(request):
    api = WeatherAPI()
    alerts = api.get_alerts(40.7128, -74.0060)  # Example coordinates for New York City
    return JsonResponse({'alerts': alerts})


def get_weather_data(request):
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    api_key = "45b01a7f6a9893cc9370a6fd91f105fb"
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric"
    
    response = requests.get(url)
    data = response.json()

    return JsonResponse({
        'city_name': data['name'],
        'temp': data['main']['temp'],
        'temp_max': data['main']['temp_max'],
        'temp_min': data['main']['temp_min'],
        'description': data['weather'][0]['description'],
        'icon': data['weather'][0]['icon'],
        'humidity': data['main']['humidity'],
        'precipitation': data['rain']['1h'] if 'rain' in data else 0,
        'wind': data['wind']['speed']
    })



@login_required
def mod_agentlist(request):
    try:
        # Get the Users instance associated with the current user
        user = Users.objects.get(id=request.user.id)
        
        # Get the Moderator instance associated with the current user
        moderator = Moderator.objects.get(user=user)
        
        # Get agents associated with this moderator
        agents = Agent.objects.filter(moderator=moderator)
        
        context = {
            'moderator_name': f"{moderator.first_name} {moderator.last_name}" or f"{user.first_name} {user.last_name}",
            'agents': agents,
        }
        
        return render(request, 'mod_agentlist.html', context)
    except Users.DoesNotExist:
        context = {'error_message': 'User not found.'}
    except Moderator.DoesNotExist:
        context = {'error_message': 'You are not registered as a moderator.'}
    
    return render(request, 'mod_agentlist.html', context)

                

@login_required
@require_POST
def save_agent_job(request):
    try:
        bus_id = request.POST.get('bus_id')
        selected_stop = request.POST.get('selected_stop')

        agent = Agent.objects.get(user=request.user)
        bus = Bus.objects.get(bus_id=bus_id)

        job = AgentJob.objects.create(
            agent=agent,
            bus=bus,
            selected_stop=selected_stop,
            status='Pending'
        )

        # Notify moderator about the new job request
        notify_moderator(job)

        return JsonResponse({'success': True, 'job_id': job.job_id, 'message': 'Job request sent to moderator for approval.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



def notify_moderator(job):
    # Implement notification logic here (e.g., email, in-app notification)
    # For now, we'll just print a message
    print(f"New job request: Job ID {job.job_id} from Agent {job.agent.first_name} {job.agent.last_name}")



from django.shortcuts import render

@login_required
def moderator_job_requests(request):
    filter_type = request.GET.get('filter', 'all')
    
    try:
        moderator = Moderator.objects.get(user=request.user)
    except Moderator.DoesNotExist:
        return render(request, 'moderator_job_requests.html', {'error': 'Moderator not found'})

    agents = Agent.objects.filter(moderator=moderator)
    
    if filter_type == 'approved':
        job_requests = AgentJob.objects.filter(agent__in=agents, status='Approved')
    elif filter_type == 'pending':
        job_requests = AgentJob.objects.filter(agent__in=agents, status='Pending')
    else:
        job_requests = AgentJob.objects.filter(agent__in=agents)
    
    job_requests_data = [
        {
            'job_id': jr.job_id,
            'agent_name': f"{jr.agent.first_name} {jr.agent.last_name}",
            'bus_name': jr.bus.bus_name,
            'selected_stop': jr.selected_stop,
            'status': jr.status,
            'date_assigned': jr.date_assigned.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for jr in job_requests
    ]
    
    context = {
        'job_requests': job_requests_data,
        'moderator_name': f"{moderator.first_name} {moderator.last_name}",
        'filter_type': filter_type,
    }
    
    return render(request, 'moderator_job_requests.html', context)



@login_required
@require_POST
def process_job_request(request):
    if not hasattr(request.user, 'moderator'):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    job_id = request.POST.get('job_id')
    action = request.POST.get('action')
    
    try:
        job_request = AgentJob.objects.get(job_id=job_id)
        
        if action == 'approve':
            job_request.status = 'Approved'
            message = "Job request approved successfully."
        elif action == 'reject':
            job_request.status = 'Rejected'
            message = "Job request rejected successfully."
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})
        
        job_request.save()

        # Prepare email context
        context = {
            'agent_name': job_request.agent.first_name,
            'bus_name': job_request.bus.bus_name,
            'selected_stop': job_request.selected_stop,
            'job_id': job_request.job_id
        }

        # Render email content from template
        template = 'emails/job_approved.html' if action == 'approve' else 'emails/job_rejected.html'
        email_content = render_to_string(template, context)

        # Send email
        send_mail(
            f"Job Request {action.capitalize()}d",
            email_content,
            settings.DEFAULT_FROM_EMAIL,
            [job_request.agent.email],
            fail_silently=False,
            html_message=email_content
        )

        return JsonResponse({'success': True, 'message': message})
    
    except AgentJob.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Job request not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    





@login_required
@require_http_methods(["GET", "POST"])
def safety_notification_report(request):
    agent = get_object_or_404(Agent, user=request.user)
    
    # Get the current active job for the agent
    current_job = AgentJob.objects.filter(
        agent=agent,
        status='Approved',
        bus__arrival_date__gte=timezone.now()
    ).order_by('-date_assigned').first()

    if not current_job:
        messages.error(request, "You don't have an active job to submit a safety report.")
        return redirect('agent_welcome')

    if request.method == 'POST':
        form_data = request.POST
        files = request.FILES.getlist('files[]')
        
        try:
            with transaction.atomic():
                # Extract form data
                report_title = form_data.get('report_title')
                incident_datetime = form_data.get('incident_datetime')
                location = form_data.get('location')
                latitude = form_data.get('latitude') or None
                longitude = form_data.get('longitude') or None
                bus_id = form_data.get('bus_id')
                stop = form_data.get('stop')
                incident_type = form_data.get('incident_type')
                severity_level = form_data.get('severity_level')
                description = form_data.get('description')

                # Get the Bus object
                try:
                    bus = Bus.objects.get(pk=bus_id)
                except Bus.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'The selected bus does not exist. Please choose a valid bus.'
                    }, status=400)

                # Convert incident_datetime to a timezone-aware datetime
                if incident_datetime:
                    incident_datetime = timezone.make_aware(datetime.strptime(incident_datetime, '%Y-%m-%dT%H:%M'))
                else:
                    incident_datetime = timezone.now()

                # Create the report
                report = SafetyNotificationReport.objects.create(
                    agent=agent,
                    report_title=report_title,
                    incident_datetime=incident_datetime,
                    location=location,
                    latitude=latitude,
                    longitude=longitude,
                    bus=bus,
                    stop=stop,
                    incident_type=incident_type,
                    severity_level=severity_level,
                    description=description,
                    status='Pending',  # Set the initial status to 'Pending'
                    route=f"{bus.departure_location} - {bus.destination_location}",
                    schedule_version=bus.schedule_version
                )

                # Handle file uploads
                for file in files:
                    SafetyReportMedia.objects.create(report=report, file=file)

                # Send automatic message to moderator
                moderator = agent.moderator
                ChatMessage.objects.create(
                    sender=agent.user,
                    recipient=moderator.user,
                    content=f"Alert: A new safety notification has been submitted. Report ID: {report.report_id}"
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Report submitted successfully.',
                    'report_id': report.report_id
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    context = {
        'agent': agent,
        'agent_id': agent.agent_id,
        'contact_info': agent.mobile,
        'route': f"{current_job.bus.departure_location} - {current_job.bus.destination_location}",
        'assigned_stop': current_job.selected_stop,
        'all_stops': current_job.bus.stops.split(',') if current_job.bus.stops else [],
        'assigned_bus': current_job.bus,
        'buses': [current_job.bus],
    }
    return render(request, 'safety_notification_report.html', context)



@login_required
def notifications_report(request):
    try:
        moderator = Moderator.objects.get(user=request.user)
        moderator_name = f"{moderator.first_name} {moderator.last_name}"
        
        # Fetch safety reports for agents under this moderator, ordered by creation date
        safety_reports = SafetyNotificationReport.objects.filter(
            agent__moderator=moderator
        ).order_by('-submitted_at')
        
    except Moderator.DoesNotExist:
        moderator_name = "Moderator"
        safety_reports = []

    context = {
        'moderator_name': moderator_name,
        'safety_reports': safety_reports,
    }
    return render(request, 'notifications_report.html', context)


from datetime import datetime, time

@login_required
def view_notification_report(request, report_id):
    report = get_object_or_404(SafetyNotificationReport, report_id=report_id)
    print(f"Debug: Fetched report with ID {report_id}")
    print(f"Debug: Bus ID: {report.bus.bus_id}")

    # Debug bus information
    if report.bus:
        print(f"Debug: Bus Name: {report.bus.bus_name}")
        print(f"Debug: Bus Number: {report.bus.bus_number}")
        print(f"Debug: Bus Route: {report.bus.departure_location} to {report.bus.destination_location}")
        print(f"Debug: Bus Stops: {report.bus.stops}")
        print(f"Debug: Bus Departure Date: {report.bus.date}")
        print(f"Debug: Bus Arrival Date: {report.bus.arrival_date}")
        print(f"Debug: Incident Date: {report.incident_datetime.date()}")
    else:
        print("Debug: No bus associated with this report")

    moderator_name = f"{request.user.first_name} {request.user.last_name}" if request.user.is_authenticated else "Unknown"
    print(f"Debug: Moderator name: {moderator_name}")

    media_files = SafetyReportMedia.objects.filter(report=report)
    print(f"Debug: Number of media files: {media_files.count()}")
    for media in media_files:
        print(f"Debug: Media file path: {media.file.url}")

    customer_details = []
    if report.bus:
        # Find all paid bookings for this bus and specific schedule version
        paid_bookings = BusBooking.objects.filter(
            bus=report.bus,
            payment_status='Paid',
            schedule_version=report.bus.schedule_version
        )
        print(f"Debug: Number of paid bookings: {paid_bookings.count()}")
        
        for booking in paid_bookings:
            customer = booking.customer
            customer_details.append({
                'name': f"{customer.first_name} {customer.last_name}",
                'email': customer.email,
                'phone': customer.phone,
                'booking_id': booking.booking_id,
                'seat_numbers': booking.seat_booked,
                'departure_date': report.bus.date,
                'payment_amount': booking.total_amount,
                'payment_date': booking.booking_date,
            })
            print(f"Debug: Added customer {customer.first_name} {customer.last_name}")
            print(f"Debug: Booking departure date: {report.bus.date}")

    print(f"Debug: Number of customer details: {len(customer_details)}")

    context = {
        'report': report,
        'media_files': media_files,
        'customer_details': customer_details,
        'moderator_name': moderator_name,
        'departure_date': report.bus.date if report.bus else None,
    }
    return render(request, 'view_notification_report.html', context)





@require_POST
def toggle_bus_status(request, bus_id):
    try:
        bus = Bus.objects.get(pk=bus_id)
        
        if bus.should_be_under_maintenance():
            bus.status = 'under_maintenance'
        else:
            bus.status = 'active' if bus.status == 'under_maintenance' else 'under_maintenance'
        
        bus.save()
        return JsonResponse({'status': 'success', 'new_status': bus.status})
    except Bus.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Bus not found'}, status=404)
    
    


import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from home.models import Notification

logger = logging.getLogger(__name__)

@login_required
@require_POST
def process_report(request):
    report_id = request.POST.get('report_id')
    action = request.POST.get('action')
    logger.info(f"Processing report with ID: {report_id}, Action: {action}")
    try:
        report = SafetyNotificationReport.objects.get(report_id=report_id)
        if report.status != 'Pending':
            logger.warning(f"Report {report_id} has already been processed")
            return JsonResponse({'success': False, 'error': 'Report has already been processed'})
        
        if action in ['approve', 'accept']:
            report.status = 'Approved'
            report.save()
            logger.info(f"Report {report_id} status updated to Approved")
            
            # Find affected bookings
            affected_bookings = BusBooking.objects.filter(
                bus=report.bus,
                payment_status='Paid',
                schedule_version=report.schedule_version
            )
            logger.info(f"Affected bookings count: {affected_bookings.count()}")
            
            affected_customers = Customers.objects.filter(busbooking__in=affected_bookings).distinct()
            logger.info(f"Affected customers count: {affected_customers.count()}")
            
            # Create notifications and send emails for affected customers
            notifications_sent = 0
            emails_sent = 0
            
            for customer in affected_customers:
                logger.info(f"Processing customer: {customer.email}")
                try:
                    Notification.objects.create(
                        user=customer.user,
                        message=f"Safety Alert: {report.report_title}",
                        is_read=False
                    )
                    notifications_sent += 1
                    logger.info(f"Notification created for customer: {customer.email}")
                except Exception as e:
                    logger.error(f"Failed to create notification for customer {customer.email}: {str(e)}")
                
                # Prepare email content
                context = {
                    'customer_name': f"{customer.first_name} {customer.last_name}",
                    'severity_level': report.severity_level,
                    'location': report.location,
                    'description': report.description,
                    'bus_name': report.bus.bus_name,
                    'departure_location': report.bus.departure_location,
                    'destination_location': report.bus.destination_location,
                }
                email_content = render_to_string('emails/safety_alert_email.html', context)
                plain_message = strip_tags(email_content)
                
                try:
                    # Send email
                    send_mail(
                        subject="Safety Alert for Your Upcoming Trip",
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[customer.email],
                        html_message=email_content,
                        fail_silently=False,
                    )
                    logger.info(f"Email sent to {customer.email}")
                    emails_sent += 1
                except Exception as e:
                    logger.error(f"Failed to send email to {customer.email}: {str(e)}")
            
            if notifications_sent == 0:
                message = f'Report approved. No affected customers found.'
            else:
                message = f'Report approved. {notifications_sent} notifications created and {emails_sent} emails sent to affected customers.'
            logger.info(message)
        elif action == 'reject':
            report.status = 'Rejected'
            report.save()
            message = 'Report rejected.'
            logger.info(f"Report {report_id} rejected")
        else:
            logger.error(f"Invalid action '{action}' for report {report_id}")
            return JsonResponse({'success': False, 'error': 'Invalid action'})
        
        return JsonResponse({
            'success': True, 
            'message': message
        })
    except SafetyNotificationReport.DoesNotExist:
        logger.error(f"Report with ID {report_id} not found")
        return JsonResponse({'success': False, 'error': 'Report not found'})
    except Exception as e:
        logger.exception(f"Error processing report: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})



def debug_notification(request, report_id):
    result = send_safety_notification(report_id)
    return HttpResponse(f"Debug result: {result} notifications sent")



logger = logging.getLogger(__name__)


def mod_agentdetails(request, agent_id):
    try:
        agent = get_object_or_404(Agent, agent_id=agent_id)
        data = {
            'first_name': agent.first_name,
            'last_name': agent.last_name,
            'email': agent.email,
            'mobile': agent.mobile,
            'address': agent.address if hasattr(agent, 'address') else None,
            'city': agent.city if hasattr(agent, 'city') else None,
            'district': agent.district if hasattr(agent, 'district') else None,
            'date_joined': agent.created_at.strftime('%Y-%m-%d') if agent.created_at else None,
            'company': agent.company,
            'location': agent.location,
            'status': agent.status,
            'profile_image': agent.profile_image.url if agent.profile_image else None,
            'document_link': agent.document.url if agent.document else None,
        }
        return JsonResponse(data)
    except ObjectDoesNotExist:
        logger.error(f"Agent with ID {agent_id} not found")
        return JsonResponse({'error': 'Agent not found'}, status=404)
    except Exception as e:
        logger.exception(f"Error fetching agent details for ID {agent_id}: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
    


@login_required
def agent_view_reports(request):
    try:
        agent = Agent.objects.get(user=request.user)
        reports = SafetyNotificationReport.objects.filter(agent=agent).order_by('-incident_datetime')
        return render(request, 'agent_view_reports.html', {'reports': reports, 'agent': agent})
    except Agent.DoesNotExist:
        messages.error(request, "Agent profile not found.")
        return redirect('agent_welcome')  # or another appropriate page
    



@login_required
@require_POST
def send_chat_message(request):
    content = request.POST.get('content')
    recipient_id = request.POST.get('recipient_id')
    
    if not content or not recipient_id:
        return JsonResponse({'status': 'error', 'message': 'Missing content or recipient'})
    
    try:
        recipient = Users.objects.get(id=recipient_id)
        message = ChatMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content
        )
        return JsonResponse({
            'status': 'success',
            'message_id': message.id,
            'timestamp': message.timestamp.isoformat()
        })
    except Users.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Recipient not found'})



@login_required
def get_chat_messages(request):
    other_user_id = request.GET.get('other_user_id')
    
    if not other_user_id:
        return JsonResponse({'status': 'error', 'message': 'Missing other_user_id'})
    
    try:
        other_user = Users.objects.get(id=other_user_id)
        messages = ChatMessage.objects.filter(
            (Q(sender=request.user, recipient=other_user) |
             Q(sender=other_user, recipient=request.user))
        ).order_by('timestamp')
        
        return JsonResponse({
            'status': 'success',
            'messages': [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'sender_id': msg.sender_id,
                    'timestamp': msg.timestamp.isoformat()
                } for msg in messages
            ]
        })
    except Users.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'})



@login_required
def get_chat_users(request):
    user = request.user
    if hasattr(user, 'agent_profile'):
        moderator = user.agent_profile.moderator
        return JsonResponse({
            'status': 'success',
            'users': [{
                'id': moderator.user.id,
                'name': f"{moderator.first_name} {moderator.last_name}",
                'role': 'Moderator',
                'avatar_url': moderator.profile_image.url if moderator.profile_image else None
            }]
        })
    elif hasattr(user, 'moderator'):
        agents = user.moderator.agents.all()
        return JsonResponse({
            'status': 'success',
            'users': [{
                'id': agent.user.id,
                'name': f"{agent.first_name} {agent.last_name}",
                'role': 'Agent',
                'avatar_url': agent.profile_image.url if agent.profile_image else None
            } for agent in agents]
        })
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid user type'})



@login_required
def get_new_messages(request):
    other_user_id = request.GET.get('other_user_id')
    last_message_id = request.GET.get('last_message_id')
    
    if not other_user_id or not last_message_id:
        return JsonResponse({'status': 'error', 'message': 'Missing parameters'})
    
    try:
        other_user = Users.objects.get(id=other_user_id)
        new_messages = ChatMessage.objects.filter(
            (Q(sender=request.user, recipient=other_user) |
             Q(sender=other_user, recipient=request.user)),
            id__gt=last_message_id
        ).order_by('timestamp')
        
        return JsonResponse({
            'status': 'success',
            'messages': [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'sender_id': msg.sender_id,
                    'timestamp': msg.timestamp.isoformat()
                } for msg in new_messages
            ],
            'server_time': now().isoformat()
        })
    except Users.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'})
    



@require_POST
def check_email(request):
    email = request.POST.get('email')
    current_user_email = request.user.email
    exists = Agent.objects.filter(email=email).exclude(email=current_user_email).exists()
    return JsonResponse({'exists': exists})



@login_required
def agent_profile_update(request):
    try:
        agent = Agent.objects.get(user=request.user)
    except Agent.DoesNotExist:
        messages.error(request, "Agent profile not found.")
        return redirect('agent_welcome')

    if request.method == 'POST':
        try:
            # Extract form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            mobile = request.POST.get('mobile')
            address = request.POST.get('address')
            city = request.POST.get('city')
            district = request.POST.get('district')

            # Check if email already exists
            if Agent.objects.filter(email=email).exclude(user=request.user).exists():
                return JsonResponse({'success': False, 'error': 'This email is already registered.'})

            # Update agent information
            agent.first_name = first_name
            agent.last_name = last_name
            agent.email = email
            agent.mobile = mobile
            agent.address = address
            agent.city = city
            agent.district = district

            # Handle profile image upload
            if 'profile_image' in request.FILES:
                if agent.profile_image:
                    default_storage.delete(agent.profile_image.name)
                file = request.FILES['profile_image']
                filename = default_storage.save(f'agent_profiles/{file.name}', ContentFile(file.read()))
                agent.profile_image = filename

            agent.save()

            # Update the associated User model
            user = agent.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            return JsonResponse({'success': True, 'message': 'Profile updated successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'agent_profile_update.html', {'agent': agent})




@login_required
def check_current_job(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated'}, status=401)

    try:
        agent = request.user.agent_profile
    except Agent.DoesNotExist:
        return JsonResponse({'error': 'User is not an agent'}, status=403)

    current_job = AgentJob.objects.filter(
        agent=agent, 
        status='Approved',
        original_arrival_date__gte=timezone.now()
    ).order_by('-date_assigned').first()

    if current_job:
        return JsonResponse({
            'has_job': True,
            'route': f"{current_job.bus.departure_location} to {current_job.bus.destination_location}",
            'stop': current_job.selected_stop,
            'arrival_date': current_job.original_arrival_date.date().isoformat(),
        })
    else:
        return JsonResponse({'has_job': False})

@login_required
@require_POST
def complete_job(request):
    try:
        agent = request.user.agent_profile
        current_job = AgentJob.objects.filter(
            agent=agent, 
            status='Approved',
            original_arrival_date__lte=timezone.now()
        ).order_by('-date_assigned').first()

        if current_job:
            current_job.mark_as_completed()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'No current job found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})   

import logging

logger = logging.getLogger(__name__)

def mod_agent_previous_jobs(request, agent_id):
    try:
        agent = get_object_or_404(Agent, agent_id=agent_id)
        jobs = AgentJob.objects.filter(agent=agent).order_by('-date_assigned')
        
        logger.info(f"Fetching jobs for agent {agent_id}. Found {jobs.count()} jobs.")
        
        job_data = []
        for job in jobs:
            job_data.append({
                'title': f"Job for {job.bus.bus_name}",
                'date': job.date_assigned.strftime('%Y-%m-%d %H:%M'),
                'description': f"Stop: {job.selected_stop}",
                'status': job.status
            })
        
        logger.info(f"Returning {len(job_data)} jobs for agent {agent_id}")
        return JsonResponse(job_data, safe=False)
    except Exception as e:
        logger.error(f"Error fetching jobs for agent {agent_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)