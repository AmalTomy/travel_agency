from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from home.models import Moderator, Users, Customers, Agent, Bus # Changed 'Customer' to 'Customers'
import json
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import render
from home.models import Agent
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import Q
from home.models import TravelReport, ReportPhoto
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
import numpy as np
from home.models import TravelReport, ReportPhoto  # Add ReportPhoto here
from django.db import transaction
import os
from home.forms import TravelReportForm, ReportPhotoForm  
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from home.models import BusBooking, Feedback, Bus
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from home.models import Bus, BusReschedule
from django.utils import timezone

# Load the trained model
weather_model = load_model('D:/project/logU/weather_classification_model.keras')

# Get class names from the training directory
train_dir = 'D:/project/dataset/train'
weather_classes = sorted(os.listdir(train_dir))

def classify_weather(image_path):
    img = Image.open(image_path).resize((224, 224))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0

    prediction = weather_model.predict(img_array)
    predicted_class = weather_classes[np.argmax(prediction)]
    return predicted_class


def toggle_moderator_status(request, moderator_id):
    if request.method == 'POST':
        moderator = get_object_or_404(Moderator, moderator_id=moderator_id)
        user = moderator.user
        
        if user.loginstatus == 'enabled':
            user.loginstatus = 'disabled'
            action = "disabled"
        else:
            user.loginstatus = 'enabled'
            action = "enabled"
        
        user.save()
        
        messages.success(request, f"Moderator {moderator.first_name} {moderator.last_name}'s account has been {action}.")
        
    return redirect('moderator_details')



def toggle_customer_status(request, customer_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_status = data.get('status')
        
        try:
            customer = get_object_or_404(Customers, customer_id=customer_id)
            customer.user.loginstatus = new_status
            customer.user.save()
            
            # If the status is changed to 'disabled', log out the user if they're currently logged in
            if new_status == 'disabled':
                logout(request)
            
            return JsonResponse({
                'success': True,
                'new_status': new_status,
                'customer_name': f"{customer.first_name} {customer.last_name}"
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


def agent_details(request):
    agents = Agent.objects.filter(status='Approved').select_related('user').all()
    return render(request, 'agent_details.html', {'agents': agents})



@login_required
@require_POST
def toggle_agent_status(request, agent_id):
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        agent = Agent.objects.get(agent_id=agent_id)
        agent.user.loginstatus = new_status
        agent.user.save()
        
        if new_status == 'disabled':
            # Log out the agent if they're currently logged in
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            for session in sessions:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(agent.user.id):
                    session.delete()
        
        return JsonResponse({'success': True, 'new_status': agent.user.loginstatus})
    except Agent.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Agent not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

@login_required
def bus_details(request):
    buses = Bus.objects.select_related('moderator_id', 'driver_info').all()
    context = {
        'buses': buses,
    }
    return render(request, 'bus_details.html', context)



def view_details(request, bus_id):
    bus = get_object_or_404(Bus.objects.select_related('moderator_id', 'driver_info'), bus_id=bus_id)
    data = {
        'bus': {
            'bus_number': bus.bus_number,
            'bus_name': bus.bus_name,
            'bus_type': bus.bus_type,
            'seating_capacity': bus.seating_capacity,
            'route': f"{bus.departure_location} to {bus.destination_location}",
            'departure': f"{bus.date} {bus.departure_time}",
            'arrival': f"{bus.arrival_date or bus.date} {bus.arrival_time}",
            'price': str(bus.ticket_price),
            'status': bus.status,
        },
        'moderator': {
            'name': f"{bus.moderator_id.first_name} {bus.moderator_id.last_name}",
            'email': bus.moderator_id.email,
            'phone': bus.moderator_id.mobile,
            'company': bus.moderator_id.company,
        },
        'driver': {
            'name': bus.driver_info.name,
            'email': bus.driver_info.email,
            'contact': bus.driver_info.contact_number,
            'license': bus.driver_info.license.url if bus.driver_info.license else None,
            'image': bus.driver_info.image.url if bus.driver_info.image else None,
        }
    }
    return JsonResponse(data)








import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.forms import modelformset_factory
from home.models import TravelReport, ReportPhoto
from home.forms import TravelReportForm, ReportPhotoForm
from django.contrib.auth.decorators import login_required
from django.db import transaction

logger = logging.getLogger(__name__)

from django.http import JsonResponse

@login_required
def submit_travel_report(request):
    if request.method == 'POST':
        form = TravelReportForm(request.POST)
        
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.status = 'Pending'  # Set status to Pending
            report.save()
            
            weather_classification = None
            if 'photo' in request.FILES:
                image = request.FILES['photo']
                photo = ReportPhoto(report=report, image=image)
                photo.save()
                
                # Classify the weather in the image
                image_path = photo.image.path
                weather_classification = classify_weather(image_path)
                photo.classification = weather_classification
                photo.save()
                
                print(f"Photo saved: {photo.image.url}")
                print(f"Weather classification: {weather_classification}")
            else:
                print("No image uploaded")
            
            return JsonResponse({
                'success': True,
                'weather_classification': weather_classification
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = TravelReportForm()
    
    return render(request, 'submit_travel_report.html', {'form': form})

@login_required
def admin_add_news(request):
    pending_reports = TravelReport.objects.filter(status='Pending')
    return render(request, 'admin_add_news.html', {'pending_reports': pending_reports})

@login_required
def view_reports(request):
    reports = TravelReport.objects.all().order_by('-travel_date').prefetch_related('photos')
    query = request.GET.get('q')
    classification_filter = request.GET.get('classification')

    if query:
        reports = reports.filter(description__icontains=query)
    
    if classification_filter:
        reports = reports.filter(photos__classification=classification_filter).distinct()

    paginator = Paginator(reports, 10)  # Show 10 reports per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    classifications = ReportPhoto.objects.values_list('classification', flat=True).distinct()

    context = {
        'reports': page_obj,
        'query': query,
        'classifications': classifications,
        'classification_filter': classification_filter,
    }
    return render(request, 'view_reports.html', context)

def report_detail(request, report_id):
    report = get_object_or_404(TravelReport, id=report_id)
    photos = report.photos.all()
    print(f"Report ID: {report_id}")
    print(f"Number of photos: {photos.count()}")
    for photo in photos:
        print(f"Photo URL: {photo.image.url}")
    
    context = {
        'report': report,
        'photos': photos,
    }
    return render(request, 'report_detail.html', context)




@login_required
def view_feedback(request):
    return render(request, 'view_feedback.html')

from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect

@login_required
@ensure_csrf_cookie
@csrf_protect
def submit_feedback(request):
    if request.method == 'POST':
        try:
            booking_id = request.POST.get('booking_id')
            booking = get_object_or_404(BusBooking, booking_id=booking_id)
            bus = booking.bus

            # Check if feedback already exists
            if not hasattr(booking, 'feedback'):
                feedback = Feedback.objects.create(
                    booking=booking,
                    bus=bus,
                    bus_name=bus.bus_name,
                    bus_route=f"{booking.departure_location} to {booking.destination}",
                    travel_date=bus.date,
                    rating=request.POST.get('rating'),
                    comment=request.POST.get('comment'),
                    improvements=request.POST.get('improvements'),
                    recommend=request.POST.get('recommend')
                )
                message = 'Feedback submitted successfully!'
            else:
                message = 'Feedback already exists for this booking.'

            return JsonResponse({'success': True, 'message': message})
        except Exception as e:
            print(f"Error in submit_feedback: {str(e)}")
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    else:
        booking_id = request.GET.get('booking_id')
        if booking_id:
            try:
                booking = get_object_or_404(BusBooking, booking_id=booking_id)
                initial_data = {
                    'booking_id': booking.booking_id,
                    'bus_name': booking.bus.bus_name,
                    'bus_route': f"{booking.departure_location} to {booking.destination}",
                    'travel_date': booking.bus.date,  # Use the bus's date instead of departure_date
                }
            except BusBooking.DoesNotExist:
                initial_data = {}
        else:
            initial_data = {}

        return render(request, 'submit_feedback.html', {'initial_data': initial_data})


@login_required
def view_bus_bookings(request):
    try:
        moderator = Moderator.objects.get(user=request.user)
        buses = Bus.objects.filter(moderator_id=moderator.moderator_id)
        
        context = {
            'buses': buses,
        }
        
        return render(request, 'view_bus_bookings.html', context)
    except Moderator.DoesNotExist:
        # Handle the case where the user is not a moderator
        context = {
            'error': 'You are not authorized to view this page.'
        }
        return render(request, 'error.html', context)

# from django.http import JsonResponse
# from django.contrib.auth.decorators import login_required
# from home.models import Bus, BusReschedule

# from django.db.models import F
# from django.http import JsonResponse
# from django.contrib.auth.decorators import login_required

# @login_required
# def get_bus_schedules(request, bus_id):
#     try:
#         bus = Bus.objects.get(pk=bus_id)
#         current_schedule = {
#             'schedule_version': bus.schedule_version,
#             'departure_location': bus.departure_location,
#             'destination_location': bus.destination_location,
#             'departure_date': bus.date.strftime('%Y-%m-%d'),
#             'departure_time': bus.departure_time.strftime('%H:%M'),
#             'ticket_price': str(bus.ticket_price),
#         }
        
#         reschedules = BusReschedule.objects.filter(bus=bus).order_by('-rescheduled_at')
        
#         schedules = [current_schedule]
#         for reschedule in reschedules:
#             schedules.append({
#                 'schedule_version': reschedule.schedule_version,
#                 'departure_location': reschedule.new_departure_location,
#                 'destination_location': reschedule.new_destination_location,
#                 'departure_date': reschedule.new_departure_date.strftime('%Y-%m-%d'),
#                 'departure_time': reschedule.new_departure_time.strftime('%H:%M'),
#                 'ticket_price': str(reschedule.new_ticket_price),
#             })
        
#         return JsonResponse({
#             'success': True,
#             'schedules': schedules
#         })
#     except Bus.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'Bus not found'}, status=404)
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def get_bus_schedules(request, bus_id):
    try:
        logger.info(f"Fetching schedules for bus {bus_id}")
        bus = Bus.objects.get(pk=bus_id)
        
        # Get all reschedules for this bus
        reschedules = BusReschedule.objects.filter(bus=bus).order_by('-schedule_version')
        
        schedules_data = []
        
        # Add the current schedule
        schedules_data.append({
            'schedule_version': bus.schedule_version,
            'departure_location': bus.departure_location,
            'destination_location': bus.destination_location,
            'departure_date': bus.date.strftime('%Y-%m-%d'),
            'departure_time': bus.departure_time.strftime('%H:%M'),
            'ticket_price': str(bus.ticket_price)
        })
        
        # Add all previous schedules
        for reschedule in reschedules:
            schedules_data.append({
                'schedule_version': reschedule.schedule_version,
                'departure_location': reschedule.old_departure_location,
                'destination_location': reschedule.old_destination_location,
                'departure_date': reschedule.old_departure_date.strftime('%Y-%m-%d'),
                'departure_time': reschedule.old_departure_time.strftime('%H:%M'),
                'ticket_price': str(reschedule.old_ticket_price)
            })
        
        # Sort schedules by version in descending order
        schedules_data.sort(key=lambda x: x['schedule_version'], reverse=True)
        
        logger.info(f"Successfully retrieved {len(schedules_data)} schedules for bus {bus_id}")
        return JsonResponse({
            'success': True,
            'schedules': schedules_data
        })
    except Bus.DoesNotExist:
        logger.error(f"Bus with id {bus_id} not found")
        return JsonResponse({'success': False, 'error': 'Bus not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_bus_schedules for bus {bus_id}: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

import logging

logger = logging.getLogger(__name__)

@login_required
def get_bus_bookings(request, bus_id):
    try:
        logger.info(f"Fetching bookings for bus {bus_id}")
        bus = Bus.objects.get(pk=bus_id)
        schedule_version = request.GET.get('schedule_version')
        logger.info(f"Schedule version: {schedule_version}")
        
        bookings = BusBooking.objects.filter(
            bus=bus,
            payment_status='Paid'
        ).select_related('customer')
        
        if schedule_version:
            try:
                schedule_version = int(schedule_version)
                bookings = bookings.filter(schedule_version=schedule_version)
            except ValueError:
                logger.warning(f"Invalid schedule_version format: {schedule_version}")
        
        logger.info(f"Number of bookings found: {bookings.count()}")
        
        booking_data = []
        for booking in bookings:
            payment = Payment.objects.filter(booking=booking, status='completed').first()
            if payment:
                booking_data.append({
                    'booking_id': booking.booking_id,
                    'customer_name': f"{booking.customer.first_name} {booking.customer.last_name}",
                    'seat_numbers': booking.seat_booked,
                    'total_amount': str(booking.total_amount),
                    'booking_date': booking.booking_date.strftime('%Y-%m-%d %H:%M'),
                    'payment_method': payment.payment_method,
                    'payment_date': payment.payment_date.strftime('%Y-%m-%d %H:%M'),
                    'schedule_version': booking.schedule_version,
                })
        
        return JsonResponse({
            'success': True, 
            'bookings': booking_data,
        })
    except Bus.DoesNotExist:
        logger.error(f"Bus with id {bus_id} not found")
        return JsonResponse({'success': False, 'error': 'Bus not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_bus_bookings: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# from django.contrib.auth.decorators import login_required
# from django.http import JsonResponse
# from home.models import Bus, BusBooking, Payment

# import logging
# from django.contrib.auth.decorators import login_required
# from django.http import JsonResponse
# from home.models import Bus, BusReschedule, BusBooking, Payment
# from django.utils import timezone

# logger = logging.getLogger(__name__)

# @login_required
# def get_bus_schedules(request, bus_id):
#     try:
#         bus = Bus.objects.get(pk=bus_id)
#         schedules = BusReschedule.objects.filter(bus=bus).order_by('-schedule_version')
        
#         # Add the current schedule
#         schedules_data = [{
#             'schedule_version': bus.schedule_version,
#             'departure_location': bus.departure_location,
#             'destination_location': bus.destination_location,
#             'departure_date': bus.date.strftime('%Y-%m-%d'),
#             'departure_time': bus.departure_time.strftime('%H:%M'),
#         }]
        
#         # Add previous schedules
#         for schedule in schedules:
#             schedules_data.append({
#                 'schedule_version': schedule.schedule_version,
#                 'departure_location': schedule.new_departure_location,
#                 'destination_location': schedule.new_destination_location,
#                 'departure_date': schedule.new_departure_date.strftime('%Y-%m-%d'),
#                 'departure_time': schedule.new_departure_time.strftime('%H:%M'),
#             })
        
#         logger.info(f"Successfully retrieved schedules for bus {bus_id}")
#         return JsonResponse({
#             'success': True,
#             'schedules': schedules_data
#         })
#     except Bus.DoesNotExist:
#         logger.error(f"Bus with id {bus_id} not found")
#         return JsonResponse({'success': False, 'error': 'Bus not found'}, status=404)
#     except Exception as e:
#         logger.error(f"Error in get_bus_schedules for bus {bus_id}: {str(e)}", exc_info=True)
#         return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)

# @login_required
# def get_bus_bookings(request, bus_id):
#     try:
#         bus = Bus.objects.get(pk=bus_id)
#         schedule_version = request.GET.get('schedule_version')
        
#         bookings = BusBooking.objects.filter(
#             bus=bus,
#             payment_status='Paid'
#         ).select_related('customer')
        
#         if schedule_version:
#             bookings = bookings.filter(schedule_version=schedule_version)
        
#         booking_data = []
#         for booking in bookings:
#             payment = Payment.objects.filter(booking=booking, status='completed').first()
#             if payment:
#                 booking_data.append({
#                     'booking_id': booking.booking_id,
#                     'customer_name': f"{booking.customer.first_name} {booking.customer.last_name}",
#                     'seat_numbers': booking.seat_booked,
#                     'total_amount': str(booking.total_amount),
#                     'booking_date': booking.booking_date.strftime('%Y-%m-%d %H:%M'),
#                     'payment_method': payment.payment_method,
#                     'payment_date': payment.payment_date.strftime('%Y-%m-%d %H:%M'),
#                     'schedule_version': booking.schedule_version,
#                 })
        
#         logger.info(f"Successfully retrieved bookings for bus {bus_id}")
#         return JsonResponse({
#             'success': True, 
#             'bookings': booking_data,
#         })
#     except Bus.DoesNotExist:
#         logger.error(f"Bus with id {bus_id} not found")
#         return JsonResponse({'success': False, 'error': 'Bus not found'}, status=404)
#     except Exception as e:
#         logger.error(f"Error in get_bus_bookings for bus {bus_id}: {str(e)}", exc_info=True)
#         return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)

# @login_required
# def get_bus_schedules(request, bus_id):
#     try:
#         bus = Bus.objects.get(pk=bus_id)
#         schedules = BusReschedule.objects.filter(bus=bus).order_by('-schedule_version')
        
#         # Add the current schedule
#         schedules_data = [{
#             'schedule_version': bus.schedule_version,
#             'departure_location': bus.departure_location,
#             'destination_location': bus.destination_location,
#             'departure_date': bus.date.strftime('%Y-%m-%d'),
#             'departure_time': bus.departure_time.strftime('%H:%M'),
#         }]
        
#         # Add previous schedules
#         for schedule in schedules:
#             schedules_data.append({
#                 'schedule_version': schedule.schedule_version,
#                 'departure_location': schedule.new_departure_location,
#                 'destination_location': schedule.new_destination_location,
#                 'departure_date': schedule.new_departure_date.strftime('%Y-%m-%d'),
#                 'departure_time': schedule.new_departure_time.strftime('%H:%M'),
#             })
        
#         return JsonResponse({
#             'success': True,
#             'schedules': schedules_data
#         })
#     except Bus.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'Bus not found'}, status=404)
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def approve_report(request, report_id):
    try:
        report = get_object_or_404(TravelReport, id=report_id)
        report.status = 'Approved'
        report.save()

        # Send email to the customer
        send_mail(
            'Your Travel Report has been Approved',
            'The report you have submitted has been successfully reviewed and accepted and has been uploaded in the blogs category. Thank you for your travel and services. Travel with us again.',
            settings.DEFAULT_FROM_EMAIL,
            [report.user.email],
            fail_silently=False,
        )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def reject_report(request, report_id):
    try:
        report = get_object_or_404(TravelReport, id=report_id)
        report.status = 'Rejected'
        report.save()

        # Send email to the customer
        send_mail(
            'Your Travel Report has been Rejected',
            'We regret to inform you that the travel report you submitted has been rejected. If you have any questions, please contact our support team.',
            settings.DEFAULT_FROM_EMAIL,
            [report.user.email],
            fail_silently=False,
        )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.templatetags.static import static
from home.models import TravelReport, ReportPhoto
from home.utils import classify_weather  # Make sure this utility function exists

@login_required
def blogs(request):
    approved_reports = TravelReport.objects.filter(status='Approved').prefetch_related('photos').order_by('-travel_date')
    default_image_url = static('images/default_user.png')
    
    # Add weather classification to each report
    for report in approved_reports:
        report.weather_classification = classify_weather(report.photos.first().image.path) if report.photos.exists() else "Unknown"
    
    context = {
        'approved_reports': approved_reports,
        'default_image_url': default_image_url,
    }
    return render(request, 'blogs.html', context)

WEATHER_PARAGRAPHS = {
    'Sunny': [
        "The journey from {departure} to {destination} was blessed with glorious sunshine. The clear skies and warm rays created the perfect backdrop for our travel, highlighting the scenic beauty along the way. The sunny weather lifted everyone's spirits, making the trip a delightful experience.",
        "Our trip from {departure} to {destination} was bathed in brilliant sunshine. The golden rays illuminated the landscape, revealing vibrant colors and breathtaking vistas. The sunny conditions made for perfect sightseeing weather, allowing us to fully appreciate the beauty of our surroundings.",
        "Traveling from {departure} to {destination} under a radiant sun was a joy. The bright, cloudless sky provided excellent visibility, showcasing the route's natural wonders in all their glory. The warm sunshine added an extra layer of enjoyment to our journey, making every moment memorable."
    ],
    'Cloudy': [
        "As we traveled from {departure} to {destination}, a blanket of clouds accompanied us. The overcast sky provided a cool and comfortable atmosphere, perfect for sightseeing without the harsh glare of direct sunlight. The cloudy conditions added a touch of mystery to the landscape.",
        "Our journey from {departure} to {destination} was under a canopy of clouds. The soft, diffused light created a serene atmosphere, lending a dreamy quality to the scenery. The cloudy weather kept temperatures pleasant, making our travel experience quite comfortable.",
        "The route from {departure} to {destination} was shrouded in clouds, creating an atmospheric backdrop for our trip. The overcast sky added depth and dimension to the landscape, with occasional breaks in the clouds offering dramatic lighting effects. It was a photographer's dream scenario."
    ],
    'Lightning': [
        "Our trip from {departure} to {destination} was marked by an electrifying display of nature's power. The lightning illuminated the sky, creating a dramatic and unforgettable journey. While it added an element of excitement, we ensured to take all necessary safety precautions.",
        "The journey between {departure} and {destination} featured a spectacular lightning show. Bolts of electricity danced across the sky, illuminating the landscape in brief, brilliant flashes. It was a awe-inspiring reminder of nature's raw energy, observed from the safety of our vehicle.",
        "As we traveled from {departure} to {destination}, the sky came alive with lightning. The electric display painted the clouds in shades of purple and white, creating a mesmerizing backdrop for our journey. It was a thrilling, albeit cautious, travel experience."
    ],
    'Rainy': [
        "The journey from {departure} to {destination} was accompanied by a gentle rainfall. The pitter-patter of raindrops created a soothing soundtrack to our travel, while the misty landscapes offered a romantic and refreshing view. The rain washed the world clean, making colors more vivid and the air crisp.",
        "Our trip from {departure} to {destination} unfolded under a steady rain. The precipitation added a reflective sheen to the roads and surrounding nature, creating beautiful mirror-like effects. The rain-soaked scenery had a unique charm, transforming familiar landscapes into something magical.",
        "Raindrops accompanied us from {departure} to {destination}, turning our journey into a cozy adventure. The gentle shower created a calming atmosphere inside our vehicle, while outside, the world seemed refreshed and renewed. The rain brought out rich earthy scents and intensified the greens of the passing landscape."
    ],
    'Sandstorm': [
        "Our travel from {departure} to {destination} encountered an impressive sandstorm. The swirling sands created an otherworldly atmosphere, reminiscent of desert adventures. While challenging, it offered a unique perspective on the raw power of nature and the ever-changing landscape.",
        "The route between {departure} and {destination} led us through a dramatic sandstorm. Visibility was reduced as the air filled with fine particles, creating an eerie, amber-lit environment. It was a stark reminder of nature's force and the unique challenges of desert travel.",
        "Our journey from {departure} to {destination} was marked by an unexpected sandstorm. The swirling sands transformed the familiar landscape into an alien terrain, with dunes shifting and reforming before our eyes. It was a humbling experience that showcased the dynamic nature of desert environments."
    ],
    'Snowy': [
        "The route from {departure} to {destination} was transformed into a winter wonderland. Snowflakes danced in the air, coating the landscape in a pristine white blanket. The snowy conditions added a magical touch to our journey, though it also required careful and cautious travel.",
        "Our trip from {departure} to {destination} was through a beautiful snowscape. The world seemed hushed under its white covering, with snow-laden trees and glistening fields creating a serene and picturesque journey. The snowy weather turned our travel into a true winter adventure.",
        "Traveling from {departure} to {destination}, we were treated to a stunning snowy panorama. The falling snow created a mesmerizing effect, like traveling through a snow globe. While it required extra caution on the roads, the breathtaking beauty of the snow-covered landscape made every moment special."
    ]
}

import random
@login_required
def blog_detail(request, report_id):
    report = get_object_or_404(TravelReport, id=report_id, status='Approved')
    photos = report.photos.all()
    
    weather_classification = classify_weather(report.photos.first().image.path) if report.photos.exists() else "Unknown"
    
    weather_paragraphs = WEATHER_PARAGRAPHS.get(weather_classification, ["The weather during our journey from {departure} to {destination} was varied and interesting, adding to the overall travel experience."])
    weather_paragraph = random.choice(weather_paragraphs).format(departure=report.departure, destination=report.destination)
    
    data = {
        'departure': report.departure,
        'destination': report.destination,
        'travel_date': report.travel_date.strftime('%Y-%m-%d'),
        'description': report.description,
        'weather_classification': weather_classification,
        'weather_paragraph': weather_paragraph,
        'photos': [{'image': photo.image.url, 'caption': photo.caption} for photo in photos],
        'user_name': f"{report.user.first_name} {report.user.last_name}",
        'user_profile_image': report.user.customer_profile.profile_picture.url if hasattr(report.user, 'customer_profile') and report.user.customer_profile.profile_picture else None
    }
    
    return JsonResponse(data)


from django.http import JsonResponse
from django.utils import timezone
from ..models import Bus  # Adjust this import based on your project structure

# ... existing code ...

def get_available_routes(request):
    current_date = timezone.now()
    available_buses = Bus.objects.filter(arrival_date__gt=current_date)
    
    routes = [
        {
            'departure': bus.departure,
            'destination': bus.destination,
            'arrival_date': bus.arrival_date.strftime('%Y-%m-%d %H:%M')
        }
        for bus in available_buses
    ]
    
    return JsonResponse({'routes': routes})

from django.shortcuts import render
from home.models import BusBooking

@login_required
def booking_cancellation(request):
    try:
        customer = Customers.objects.get(user__email=request.user.email)
        bookings = BusBooking.objects.filter(customer=customer, payment_status='Paid').order_by('-booking_date')

        # Search functionality
        query = request.GET.get('search')
        if query:
            bookings = bookings.filter(
                Q(booking_id__icontains=query) |
                Q(departure_location__icontains=query) |
                Q(destination__icontains=query)
            )

        # Pagination
        paginator = Paginator(bookings, 10)  # Show 10 bookings per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'booking_cancellation.html', {'bookings': page_obj, 'query': query})
    except Customers.DoesNotExist:
        return render(request, 'booking_cancellation.html', {'error': 'No customer profile found for this user.'})


from django.db import transaction
from decimal import Decimal  # Add this import at the top of the file
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from home.models import BusBooking, Payment, Customers, Bus
# ... other imports ...

from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from home.models import Notification
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.db.models import F  # Add this import at the top of the file

@login_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        with transaction.atomic():
            booking = get_object_or_404(BusBooking, booking_id=booking_id, customer__user=request.user)
            
            if booking.is_cancellable():
                # Calculate refund amount (65% of total)
                refund_amount = booking.total_amount * Decimal('0.65')
                
                # Update booking status
                booking.payment_status = 'Cancelled'
                booking.save()
                
                # Update payment status
                payment = Payment.objects.filter(booking=booking, status='completed').first()
                refund_date = timezone.now()
                if payment:
                    payment.status = 'cancelled'
                    payment.refund_amount = refund_amount
                    payment.refund_date = refund_date
                    payment.save()
                else:
                    # Create a new payment record if one doesn't exist
                    payment = Payment.objects.create(
                        booking=booking,
                        amount=booking.total_amount,
                        status='cancelled',
                        refund_amount=refund_amount,
                        refund_date=refund_date
                    )
                
                # Update available seats
                bus = booking.bus
                num_cancelled_seats = booking.num_tickets
                bus.available_seats = F('available_seats') + num_cancelled_seats
                bus.save()
                
                # Prepare email context
                email_context = {
                    'customer_name': booking.customer.first_name,
                    'bus_name': bus.bus_name,
                    'departure': bus.departure_location,
                    'destination': bus.destination_location,
                    'total_amount': booking.total_amount,
                    'refund_amount': refund_amount,
                    'refund_date': refund_date.strftime('%Y-%m-%d'),
                }
                
                # Render email template
                html_message = render_to_string('emails/cancel_booking_email.html', email_context)
                plain_message = strip_tags(html_message)
                
                # Send email
                subject = 'Booking Cancellation Confirmation'
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.customer.user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Prepare response data
                response_data = {
                    'success': True,
                    'message': f"Your booking for {bus.bus_name} from {bus.departure_location} to {bus.destination_location} has been canceled. 65% of the total amount (${refund_amount:.2f}) has been refunded to your payment method."
                }
                
                return JsonResponse(response_data)
            else:
                return JsonResponse({'success': False, 'message': f'Booking #{booking_id} is not eligible for cancellation.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from home.models import Bus, BusReschedule
from django.utils import timezone

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.utils import timezone
from home.models import Bus, BusReschedule

@login_required
@require_POST
def reschedule_bus(request):
    bus_id = request.POST.get('bus_id')
    new_departure_date = request.POST.get('date')
    new_departure_time = request.POST.get('departure_time')
    new_arrival_date = request.POST.get('arrival_date')
    new_arrival_time = request.POST.get('arrival_time')
    new_departure_location = request.POST.get('departure_location')
    new_destination_location = request.POST.get('destination_location')
    new_stops = request.POST.get('stops')
    new_ticket_price = request.POST.get('ticket_price')

    try:
        bus = Bus.objects.get(bus_id=bus_id)
        moderator = request.user.moderator  # Get the moderator from the logged-in user

        if bus.can_reschedule():
            # Create a new BusReschedule entry
            BusReschedule.objects.create(
                bus=bus,
                moderator=moderator,
                old_departure_date=bus.date,
                old_departure_time=bus.departure_time,
                old_arrival_date=bus.arrival_date,
                old_arrival_time=bus.arrival_time,
                old_departure_location=bus.departure_location,
                old_destination_location=bus.destination_location,
                old_stops=bus.stops,
                old_ticket_price=bus.ticket_price,
                new_departure_date=parse_date(new_departure_date),
                new_departure_time=new_departure_time,
                new_arrival_date=parse_date(new_arrival_date),
                new_arrival_time=new_arrival_time,
                new_departure_location=new_departure_location,
                new_destination_location=new_destination_location,
                new_stops=new_stops,
                new_ticket_price=new_ticket_price,
                schedule_version=bus.schedule_version + 1
            )

            # Update the bus with new details
            bus.date = parse_date(new_departure_date)
            bus.departure_time = new_departure_time
            bus.arrival_date = parse_date(new_arrival_date)
            bus.arrival_time = new_arrival_time
            bus.departure_location = new_departure_location
            bus.destination_location = new_destination_location
            bus.stops = new_stops
            bus.ticket_price = new_ticket_price
            bus.status = 'active'
            bus.schedule_version += 1
            bus.save()

            return JsonResponse({
                'success': True,
                'message': f'Bus {bus.bus_name} ({bus.bus_number}) has been successfully rescheduled.',
                'new_arrival_date': bus.arrival_date.isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Bus cannot be rescheduled before its arrival date.'
            })
    except Bus.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Bus not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
    
def bus_images(request, bus_id):
    try:
        bus = Bus.objects.get(bus_id=bus_id)
        
        image_data = []
        for bus_image in bus.images.all():
            image_data.append({
                'url': bus_image.image.url,
                'caption': bus_image.caption or f"Image of {bus.bus_name}"
            })

        return JsonResponse({
            'images': image_data
        })
    except Bus.DoesNotExist:
        return JsonResponse({'error': 'Bus not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def admin_bus_bookings(request):
    moderators = Moderator.objects.all()
    
    moderator_data = []
    for moderator in moderators:
        bus_count = Bus.objects.filter(moderator_id=moderator).count()
        moderator_data.append({
            'moderator_id': moderator.moderator_id,
            'name': f"{moderator.first_name} {moderator.last_name}",
            'company_name': moderator.company,
            'bus_count': bus_count
        })
    
    context = {
        'moderator_data': moderator_data
    }
    
    return render(request, 'admin_bus_bookings.html', context)
@login_required
def admin_get_moderator_buses(request, moderator_id):
    try:
        moderator = Moderator.objects.get(moderator_id=moderator_id)
        buses = Bus.objects.filter(moderator_id=moderator)
        bus_data = [{'bus_id': bus.bus_id, 'bus_name': bus.bus_name, 'bus_number': bus.bus_number} for bus in buses]
        return JsonResponse({'buses': bus_data})
    except Moderator.DoesNotExist:
        return JsonResponse({'error': 'Moderator not found'}, status=404)

@login_required
def admin_get_bus_schedules(request, bus_id):
    try:
        bus = Bus.objects.get(bus_id=bus_id)
        schedules = BusReschedule.objects.filter(bus=bus).order_by('-schedule_version')
        
        schedules_data = [{
            'schedule_version': bus.schedule_version,
            'departure_location': bus.departure_location,
            'destination_location': bus.destination_location,
            'departure_date': bus.date.strftime('%Y-%m-%d'),
            'departure_time': bus.departure_time.strftime('%H:%M'),
        }]
        
        for schedule in schedules:
            schedules_data.append({
                'schedule_version': schedule.schedule_version,
                'departure_location': schedule.new_departure_location,
                'destination_location': schedule.new_destination_location,
                'departure_date': schedule.new_departure_date.strftime('%Y-%m-%d'),
                'departure_time': schedule.new_departure_time.strftime('%H:%M'),
            })
        
        return JsonResponse({'schedules': schedules_data})
    except Bus.DoesNotExist:
        return JsonResponse({'error': 'Bus not found'}, status=404)

@login_required
def admin_get_bus_bookings(request, bus_id, schedule_version):
    try:
        bus = Bus.objects.get(bus_id=bus_id)
        bookings = BusBooking.objects.filter(bus=bus, schedule_version=schedule_version)
        
        bookings_data = []
        for index, booking in enumerate(bookings, start=1):
            bookings_data.append({
                'serial_number': f"BK{index:04d}-{booking.booking_id}",
                'customer_name': f"{booking.customer.first_name} {booking.customer.last_name}",
                'seat_booked': booking.seat_booked,
                'total_amount': str(booking.total_amount),
                'payment_status': booking.payment_status,
            })
        
        return JsonResponse({'bookings': bookings_data})
    except Bus.DoesNotExist:
        return JsonResponse({'error': 'Bus not found'}, status=404)
    
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO

@login_required
def admin_download_bookings_pdf(request, bus_id, schedule_version):
    try:
        bus = Bus.objects.get(bus_id=bus_id)
        bookings = BusBooking.objects.filter(bus=bus, schedule_version=schedule_version)
        
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF object, using the buffer as its "file."
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Create the table data
        data = [['Booking Number', 'Customer Name', 'Seats', 'Total Amount', 'Payment Status']]
        for index, booking in enumerate(bookings, start=1):
            data.append([
                f"BK{index:04d}-{booking.booking_id}",
                f"{booking.customer.first_name} {booking.customer.last_name}",
                booking.seat_booked,
                str(booking.total_amount),
                booking.payment_status
            ])
        
        # Add style to the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table = Table(data)
        table.setStyle(style)
        
        # Add the table to the PDF
        elements = [table]
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and write it to the response
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bus_{bus_id}_schedule_{schedule_version}_bookings.pdf"'
        response.write(pdf)
        
        return response
    except Bus.DoesNotExist:
        return HttpResponse('Bus not found', status=404)
    except Exception as e:
        return HttpResponse(str(e), status=500)