from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.conf import settings
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.urls import reverse
from django.db.models import Q, F

from .models import Users, Moderator, Customers, Bus, Location
from .forms import BusForm, CustomerProfileForm

import os
import re
import json
import logging
import pandas as pd
from datetime import date, datetime

from django.core.serializers.json import DjangoJSONEncoder

# Set up logging
logger = logging.getLogger(__name__)

user = get_user_model()

@transaction.atomic
def deactivate_customer(request, customer_id):
    if request.method == 'POST':
        customer = get_object_or_404(Customers, customer_id=customer_id)
        user = customer.user
        
        # Delete the customer and associated user
        customer.delete()
        user.delete()
        
        messages.success(request, f"Customer {customer.first_name} {customer.last_name} has been deactivated and removed from the system.")
    
    return redirect('customer_details')

def index(request):
    return render(request, 'index.html')

def profile(request):
    try:
        customer = Customers.objects.get(email=request.user.email)
    except Customers.DoesNotExist:
        customer = None
    return render(request, 'profile.html', {'customer': customer})

@never_cache
def welcomePage(request):
    if not request.user.is_authenticated:
        return redirect('index')
    return render(request, 'welcome.html')

def loginn(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # print(f'Received POST request with email: {email}')
        # print(f'Received POST request with password: {password}')

        # Authenticate the user
        user = authenticate(request, username=email, password=password)
        print(f'Authentication result: {user}')

        if user is not None:
            print(f'User authenticated: {user.email}')

            # Check if the user is a moderator
            moderator = Moderator.objects.filter(email=email).first()
            print(f'Moderator check result: {moderator}')

            if moderator:
                print(f'Moderator status: {moderator.status}')

                if moderator.status == 'Pending':
                    print('Moderator registration is pending.')
                    return render(request, 'pending_registration.html', {'message': 'Your registration request is pending. After the admin accepts it, you can log in to the system.'})
                elif moderator.status == 'Rejected':
                    print('Moderator registration was rejected.')
                    return render(request, 'pending_registration.html', {'message': 'Your registration request was rejected. Please contact support for more details.'})
                elif moderator.status == 'Approved':
                    print('Moderator registration approved. Logging in.')
                    user.set_status_active()
                    auth_login(request, user)
                    return redirect('mod_home')  # Redirect to moderator home

            # Log the user in if not a moderator or no status issues
            print('Logging in as a regular user or admin.')
            user.set_status_active()
            auth_login(request, user)
            if user.email == 'admin@gmail.com':
                print('Redirecting to admin panel.')
                return redirect('admin1')
            else:
                print('Redirecting to welcome page.')
                return redirect('welcome')  # Default redirection for other user types

        else:
            print('Invalid email or password.')
            # messages.error(request, 'Invalid email or password.')
            # Redirect back to the login page on failure
            return render(request, 'login.html',{'error':'Invalid Email or Password'})

    print('GET request received, rendering login page.')
    return render(request, 'login.html')

def signout(request):
    if request.user.is_authenticated:
        request.user.set_status_inactive()
    auth_logout(request)
    return redirect('login')

def pending_registration(request):
    return render(request, 'pending_registration.html', {'message': 'Your registration request is pending. After the admin accepts it, you can log in to the system.'})

def mod_req_details(request):
    if not request.user.is_authenticated:
        return redirect('index')
    
    pending_moderators = Moderator.objects.filter(status='Pending')

    if request.method == 'POST':
        moderator_id = request.POST.get('moderator_id')
        action = request.POST.get('action')
        moderator_email = request.POST.get('moderator_email')

        if moderator_id:
            moderator = get_object_or_404(Moderator, moderator_id=moderator_id)
            if action == 'accept':
                moderator.status = 'Approved'
                moderator.save()
                messages.success(request, f'Moderator {moderator.first_name} {moderator.last_name} approved successfully.')

                # Send email
                subject = 'Your moderator request has been accepted'
                message = 'Congratulations! You can now log in to our system.'
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [moderator_email]

                try:
                    send_mail(subject, message, from_email, recipient_list)
                    messages.success(request, f'Acceptance email sent to {moderator_email}')
                except Exception as e:
                    messages.error(request, f'Failed to send email: {str(e)}')

            elif action == 'reject':
                moderator.status = 'Rejected'
                moderator.save()
                messages.error(request, f'Moderator {moderator.first_name} {moderator.last_name} rejected.')

            return redirect('mod_req_details')

    return render(request, 'mod_req_details.html', {'pending_moderators': pending_moderators})

import logging

logger = logging.getLogger(__name__)

def signup(request):
    if request.method == "POST":
        logger.info(f"Received POST data: {request.POST}")
        fname = request.POST.get('f_name')
        lname = request.POST.get('l_name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        errors = []

        if not all([fname, lname, address, phone, email, password, password_confirm]):
            errors.append("All fields are required.")

        try:
            validate_email(email)
        except ValidationError:
            errors.append("Invalid email format.")

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        if password != password_confirm:
            errors.append("Passwords do not match.")

        if Customers.objects.filter(email=email).exists():
            errors.append("This email is already registered.")

        if errors:
            return render(request, 'signup.html', {'errors': errors})

        try:
            user = Users.objects.create_user(
                username=email, 
                email=email, 
                first_name=fname, 
                last_name=lname,
                password=password, 
                user_type='customers'
            )

            # Create customer profile in Customers table
            customer = Customers(
                user=user, 
                email=email, 
                first_name=fname, 
                last_name=lname, 
                address=address, 
                phone=phone
            )
            customer.save()

            messages.success(request, 'User created successfully')
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    else:
        logger.info("Received GET request for signup page")
    return render(request, 'signup.html')

@require_POST
@csrf_protect
def check_email(request):
    email = request.POST.get('email')
    exists = Customers.objects.filter(email=email).exists() or Moderator.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

def signout(request):
    if request.user.is_authenticated:
        request.user.set_status_inactive()
    logout(request)
    return redirect('login')

def booking(request):
    if not request.user.is_authenticated:
        return redirect('index')
    return render(request, 'booking.html')

def admin1(request):
    if not request.user.is_authenticated:
        return redirect('index')
    return render(request, 'admin1.html')

def mod_reg(request):
    return render(request, 'mod_reg.html')

def mod_sch(request):
    locations = Location.objects.all().order_by('source', 'destination').values('source', 'source_code', 'destination', 'destination_code', 'stops')
    print("Number of locations:", locations.count())
    locations_json = json.dumps(list(locations), cls=DjangoJSONEncoder)
    print("Locations data:", locations_json)  # Add this line for debugging
    context = {
        'locations': locations_json,
    }
    return render(request, 'mod_sch.html', context)

def get_stops(request):
    departure = request.GET.get('departure')
    destination = request.GET.get('destination')
    
    try:
        location = Location.objects.get(source=departure, destination=destination)
        stops = location.get_stops_list()
        return JsonResponse({'success': True, 'stops': stops})
    except Location.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No routes currently available for the selected locations. Please select other locations.'})

def signup_moderator(request):
    if request.method == "POST":
        fname = request.POST['f_name']
        lname = request.POST['l_name']
        mobile = request.POST['mobile']
        email = request.POST['email']
        password = request.POST['password']
        password_confirm = request.POST.get('password_confirm', '')
        gst = request.POST.get('gst', '')
        pan = request.POST.get('pan', '')
        pan_name = request.POST.get('pan_name', '')
        aadhar = request.POST.get('aadhar', '')
        company = request.POST.get('company', '')
        city = request.POST.get('city', '')
        
        errors = {}

        if password != password_confirm:
            errors['password'] = 'Passwords do not match'
        
        if Moderator.objects.filter(email=email).exists():
            errors['email'] = 'This email is already registered'

        if errors:
            return render(request, 'mod_reg.html', {'errors': errors})
        
        try:
            with transaction.atomic():
                # Create login entry in Users table
                user = Users.objects.create_user(
                    username=email, 
                    email=email, 
                    password=password, 
                    user_type='moderator'
                )
                
                # Create moderator profile in Moderator table
                moderator = Moderator(
                    user=user,
                    first_name=fname,
                    last_name=lname,
                    mobile=mobile,
                    email=email,
                    password=make_password(password),
                    gst=gst,
                    pan=pan,
                    pan_name=pan_name,
                    aadhar=aadhar,
                    company=company,
                    city=city,
                    user_type='moderator'
                )
                
                # Handle the CV file
                if 'cv_file' in request.FILES:
                    moderator.cv_file = request.FILES['cv_file']
                
                # Save the moderator profile
                moderator.save()
            
            messages.success(request, 'Moderator created successfully')
            return redirect('login')
        except Exception as e:
            errors['general'] = f"Error: {str(e)}"
            return render(request, 'mod_reg.html', {'errors': errors})
    
    return render(request, 'mod_reg.html')

def customer_details(request):
    customers = Customers.objects.select_related('user').all()
    return render(request, 'customer_details.html', {'customers': customers})

def mod_request(request):
    return render(request, 'mod_request.html')

def moderator_details(request):
    approved_moderators = Moderator.objects.filter(status='Approved')
    return render(request, 'moderator_details.html', {'moderators': approved_moderators})

def mod_home(request):
    if not request.user.is_authenticated:
        return redirect('index')
    else:
        try:
            moderator = Moderator.objects.get(email=request.user.email)
        except Moderator.DoesNotExist:
            moderator = None

        context = {
            'first_name': moderator.first_name if moderator else '',
            'last_name': moderator.last_name if moderator else '',
        }
        return render(request, 'mod_home.html', context)

@login_required
def add_bus(request):
    if not request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = BusForm(request.POST, request.FILES)
        if form.is_valid():
            bus = form.save(commit=False)
            try:
                moderator = Moderator.objects.get(user=request.user)
                bus.moderator_id = moderator

                # Use the date from the form if provided, otherwise use today's date
                if form.cleaned_data['date']:
                    bus.date = form.cleaned_data['date']
                else:
                    bus.date = date.today()

                bus.save()
                messages.success(request, 'Bus added successfully.')
                return redirect('mod_home')
            except ObjectDoesNotExist:
                messages.error(request, 'You are not authorized to add a bus.')
            except IntegrityError as e:
                messages.error(request, f'An error occurred while saving the bus: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BusForm()

    return render(request, 'mod_sch.html', {'form': form})

@require_POST
def update_profile(request):
    try:
        customer = Customers.objects.get(email=request.user.email)

        # Server-side validation
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()

        errors = {}

        if not first_name or re.search(r'\d', first_name):
            errors['first_name'] = "First name is required and should not contain numbers."
        if not last_name or re.search(r'\d', last_name):
            errors['last_name'] = "Last name is required and should not contain numbers."
        if not email:
            errors['email'] = "Email is required."
        else:
            try:
                validate_email(email)
                # Check if email already exists for another user
                if Customers.objects.exclude(email=request.user.email).filter(email=email).exists():
                    errors['email'] = "This email is already taken."
            except ValidationError:
                errors['email'] = "Please enter a valid email address."
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            errors['phone_number'] = "Please enter a valid 10-digit phone number."
        if not address:
            errors['address'] = "Address is required."

        # Validate profile picture
        if 'profile_picture' in request.FILES:
            file = request.FILES['profile_picture']
            if not file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                errors['profile_picture'] = "Please upload an image file (jpg, jpeg, png, or gif)."

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        customer.first_name = first_name
        customer.last_name = last_name
        customer.email = email
        customer.phone = phone_number
        customer.address = address

        profile_picture_url = None
        if 'profile_picture' in request.FILES:
            file = request.FILES['profile_picture']
            file_name = default_storage.save(os.path.join('profile_pictures', file.name), ContentFile(file.read()))
            customer.profile_picture = file_name
            profile_picture_url = customer.profile_picture.url

        customer.save()

        # Update the associated User model
        user = customer.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        return JsonResponse({
            'success': True,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email,
            'phone_number': customer.phone,
            'address': customer.address,
            'profile_picture_url': profile_picture_url
        })

    except Customers.DoesNotExist:
        return JsonResponse({'success': False, 'errors': {'general': "Customer profile not found."}})
    except Exception as e:
        return JsonResponse({'success': False, 'errors': {'general': str(e)}})

def booking_page(request):
    return render(request, 'booking.html')


@login_required
def buses_added_by_moderator(request):
    try:
        moderator = Moderator.objects.get(user=request.user)
        buses = Bus.objects.filter(moderator_id=moderator)
        return render(request, 'buses_added_by_moderator.html', {'buses': buses})
    except Moderator.DoesNotExist:
        return render(request, 'error.html', {'message': 'You are not authorized to view this page.'})
    
@login_required
def edit_bus(request, bus_id):
    try:
        moderator = Moderator.objects.get(user=request.user)
        bus = Bus.objects.get(bus_id=bus_id, moderator_id=moderator)
        
        if request.method == 'POST':
            form = BusForm(request.POST, instance=bus)
            if form.is_valid():
                form.save()
                return redirect('buses_added_by_moderator')
        else:
            form = BusForm(instance=bus)
        
        return render(request, 'edit_bus.html', {'form': form, 'bus': bus})
    except (Moderator.DoesNotExist, Bus.DoesNotExist):
        return render(request, 'error.html', {'message': 'You are not authorized to edit this bus.'})
    
def delete_bus(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    bus.delete()
    return redirect('buses_added_by_moderator')

def bus_list(request):
    if request.method == 'POST':
        source = request.POST.get('departure_location')
        destination = request.POST.get('destination_location')
        date_str = request.POST.get('date')
        
        # Convert date string to date object
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Fetch bus data based on the source, destination, and date
        buses = Bus.objects.filter(
            departure_location__icontains=source,
            destination_location__icontains=destination,
            date=date
        )

        context = {
            'source': source,
            'destination': destination,
            'date': date,
            'buses': buses,
        }
        return render(request, 'bus_list.html', context)
    else:
        return render(request, 'bus_list.html')

@transaction.atomic
def deactivate_moderator(request, moderator_id):
    if request.method == 'POST':
        moderator = get_object_or_404(Moderator, moderator_id=moderator_id)
        user = moderator.user
        
        # Delete all buses associated with this moderator
        Bus.objects.filter(moderator_id=moderator).delete()
        
        # Delete the moderator and associated user
        moderator.delete()
        user.delete()
        
        messages.success(request, f"Moderator {moderator.first_name} {moderator.last_name} has been deactivated and removed from the system, along with all their associated buses.")
    
    return redirect('moderator_details')


def add_locations(request):
    if request.method == 'POST':
        try:
            source = request.POST.get('source')
            source_code = request.POST.get('source_code')
            destination = request.POST.get('destination')
            destination_code = request.POST.get('destination_code')
            stops = request.POST.getlist('stops[]')

            # Check if a similar location already exists
            existing_location = Location.objects.filter(
                Q(source=source, source_code=source_code) &
                Q(destination=destination, destination_code=destination_code)
            ).first()

            if existing_location:
                return JsonResponse({'success': False, 'message': 'This location already exists in the database.'})
            else:
                location = Location.objects.create(
                    source=source,
                    source_code=source_code,
                    destination=destination,
                    destination_code=destination_code,
                    stops=','.join(stops)
                )
                return JsonResponse({'success': True, 'message': 'Location added successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error adding location: {str(e)}'})
    
    return render(request, 'add_locations.html')

@require_POST
def upload_excel(request):
    if 'excelFile' not in request.FILES:
        return JsonResponse({'success': False, 'message': 'No file was uploaded'})

    excel_file = request.FILES['excelFile']
    
    try:
        # Save the uploaded file temporarily
        file_name = default_storage.save('temp_excel_upload.xlsx', ContentFile(excel_file.read()))
        file_path = default_storage.path(file_name)
        
        # Process the Excel file
        df = pd.read_excel(file_path)
        
        # Check if required columns exist
        required_columns = ['source', 'source_code', 'destination', 'destination_code', 'stops']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing columns in Excel file: {', '.join(missing_columns)}")
        
        locations_added = 0
        locations_skipped = 0
        for index, row in df.iterrows():
            # Check if a similar location already exists
            existing_location = Location.objects.filter(
                source=row['source'],
                source_code=row['source_code'],
                destination=row['destination'],
                destination_code=row['destination_code']
            ).first()
            
            if existing_location:
                locations_skipped += 1
                logger.info(f"Skipped duplicate location: {row['source']} to {row['destination']}")
            else:
                Location.objects.create(
                    source=row['source'],
                    source_code=row['source_code'],
                    destination=row['destination'],
                    destination_code=row['destination_code'],
                    stops=row['stops']
                )
                locations_added += 1
                logger.info(f"Added new location: {row['source']} to {row['destination']}")
        
        # Delete the temporary file
        default_storage.delete(file_name)
        
        message = f'{locations_added} locations added successfully. {locations_skipped} duplicate locations skipped.'
        logger.info(message)
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error processing Excel file: {str(e)}'})

def get_locations(request):
    try:
        locations = Location.objects.all().values('source', 'destination')
        return JsonResponse({'success': True, 'locations': list(locations)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error fetching locations: {str(e)}'})
