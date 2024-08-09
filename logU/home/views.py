from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth import get_user_model
from .models import Users,Moderator
from .models import Users, Customers
from django.contrib.auth.hashers import make_password
from .forms import BusForm
from .forms import CustomerProfileForm
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.conf import settings
import os
from django.views.decorators.cache import never_cache
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
import traceback
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import Bus
from django.core.exceptions import ObjectDoesNotExist
from datetime import date, datetime
from django.db import IntegrityError
from django.core.mail import send_mail
from django.contrib.auth import login as auth_login, logout as auth_logout
from .models import Location


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

def signup(request):
    if request.method == "POST":
        fname = request.POST.get('f_name')
        lname = request.POST.get('l_name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = Users.objects.create_user(username=email, email=email, first_name=fname, last_name=lname,password=password, user_type='customers')

            # Create customer profile in Customers table
            customer = Customers(user=user, email=email, first_name=fname, last_name=lname, address=address, phone=phone)
            customer.save()

            messages.success(request, 'User created successfully')
            return redirect('login')
        except Exception as e:
            # logger.error(f"Error during user signup: {e}")
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'signup.html')

@require_POST
@csrf_protect
def check_email(request):
    email = request.POST.get('email')
    is_taken_customer = Customers.objects.filter(email=email).exists()
    is_taken_moderator = Moderator.objects.filter(email=email).exists()
    return JsonResponse({'available': not (is_taken_customer or is_taken_moderator)})

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
    return render(request, 'mod_sch.html')

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
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'mod_reg.html')
        
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
            messages.error(request, f"Error: {str(e)}")
    
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

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

@require_POST
@csrf_exempt
def check_email(request):
    email = request.POST.get('email')
    exists = Customers.objects.filter(email=email).exists()
    return JsonResponse({'available': not exists})

def update_profile(request):
    if request.method == 'POST':
        try:
            customer = Customers.objects.get(email=request.user.email)

            # Server-side validation
            first_name = request.POST.get('first_name').strip()
            last_name = request.POST.get('last_name').strip()
            email = request.POST.get('email').strip()
            phone_number = request.POST.get('phone_number').strip()
            address = request.POST.get('address').strip()

            errors = []

            if not first_name or re.search(r'\d', first_name):
                errors.append("First name is required and should not contain numbers.")
            if not last_name or re.search(r'\d', last_name):
                errors.append("Last name is required and should not contain numbers.")
            if not email:
                errors.append("Email is required.")
            else:
                try:
                    validate_email(email)
                    # Check if email already exists for another user
                    if Customers.objects.exclude(email=request.user.email).filter(email=email).exists():
                        errors.append("This email is already taken.")
                except ValidationError:
                    errors.append("Please enter a valid email address.")
            if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
                errors.append("Please enter a valid 10-digit phone number.")
            if not address:
                errors.append("Address is required.")

            # Validate profile picture
            if 'profile_picture' in request.FILES:
                file = request.FILES['profile_picture']
                if not file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    errors.append("Please upload an image file (jpg, jpeg, png, or gif).")

            if errors:
                return JsonResponse({'success': False, 'error': ' '.join(errors)})

            customer.first_name = first_name
            customer.last_name = last_name
            customer.email = email
            customer.phone = phone_number
            customer.address = address

            if 'profile_picture' in request.FILES:
                file = request.FILES['profile_picture']
                file_name = default_storage.save(os.path.join('profile_pictures', file.name), ContentFile(file.read()))
                customer.profile_picture = file_name

            customer.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'profile_picture_url': customer.profile_picture.url if customer.profile_picture else None
                })

            return redirect('profile')

        except Customers.DoesNotExist:
            error = "Customer profile not found."
            print("Customer profile not found.")
        except Exception as e:
            error = str(e)
            print("Error: ", e)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error})

        return redirect('profile')

    return redirect('profile')

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

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from .models import Moderator, Bus

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
    return render(request, 'add_locations.html')

def add_location(request):
    if request.method == 'POST':
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        stops = request.POST.getlist('stops[]')
        
        location = Location(source=source, destination=destination)
        location.set_stops_list(stops)
        location.save()
