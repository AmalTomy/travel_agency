from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from .models import Users,Moderator
from .models import Users, Customers
from django.contrib.auth.hashers import make_password

from .models import Moderator, Customers
user = get_user_model()
def index(request):
    return render(request, 'index.html')
def welcome(request):
    return render(request, 'welcome.html')

def profile(request):
    return render(request, 'profile.html')



def loginn(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            
            # Redirect based on user type
            if user.email == 'admin@gmail.com':
                return redirect('admin1')
            elif user.user_type == 'moderator':
                return redirect('mod_sch')
            else:
                return redirect('welcome')  # Default redirection for other user types

        else:
            messages.error(request, 'Invalid email or password.')

        return redirect('login')  # Redirect back to the login page on failure

    return render(request, 'login.html')



def signup(request):
    if request.method == "POST":
        fname = request.POST['f_name']
        lname = request.POST['l_name']
        address = request.POST['address']
        phone = request.POST['phone']
        email = request.POST['email']
        password = request.POST['password']

        try:
            # Create user in Users table
            user = Users.objects.create_user(username=email, email=email, password=password, user_type='customers')

            # Create customer profile in Customers table
            customer = Customers.objects.create(email=email, first_name=fname, last_name=lname, address=address, phone=phone)
            customer.save()

            messages.success(request, 'User created successfully')
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'signup.html')


def signout(request):
    logout(request)
    return redirect('login')

def booking(request):
    return render(request, 'booking.html')

def admin1(request):
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
            # Create moderator profile in Moderator table
            moderator = Moderator(
                first_name=fname,
                last_name=lname,
                mobile=mobile,
                email=email,
                password=make_password(password),  # Hash the password
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

            # Create login entry in Users table
            user = Users.objects.create_user(username=email, email=email, password=password, user_type='moderator')
            user.save()

            messages.success(request, 'Moderator created successfully')
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'mod_reg.html')

