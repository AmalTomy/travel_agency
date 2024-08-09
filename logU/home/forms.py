# forms.py

from django import forms
from .models import Bus
from .models import Customers


class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = [
            'date', 'bus_name', 'bus_number', 'bus_type', 'seating_capacity', 
            'departure_location', 'destination_location', 'departure_time', 
            'arrival_time', 'stops', 'ticket_price', 'contact_number', 
            'email_address', 'bus_image', 'driver_information', 'status'
        ]

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customers
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']