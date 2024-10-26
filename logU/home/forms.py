# forms.py

from django import forms
from .models import Bus
from .models import Customers
from .models import SafetyNotificationReport
from .models import TravelReport, ReportPhoto, DriversInfo

class BusForm(forms.ModelForm):
    # Add fields for DriversInfo
    driver_name = forms.CharField(max_length=100)
    driver_license = forms.FileField()
    driver_email = forms.EmailField()
    driver_contact = forms.CharField(max_length=20)
    driver_image = forms.ImageField()

    class Meta:
        model = Bus
        fields = [
            'date', 'bus_name', 'bus_number', 'bus_type', 'seating_capacity', 
            'departure_location', 'destination_location', 'departure_time', 
            'arrival_time', 'arrival_date', 'stops', 'ticket_price', 
            'bus_image', 'status'
        ]

    def save(self, commit=True):
        bus = super().save(commit=False)
        if commit:
            bus.save()
            DriversInfo.objects.create(
                bus=bus,
                name=self.cleaned_data['driver_name'],
                license=self.cleaned_data['driver_license'],
                email=self.cleaned_data['driver_email'],
                contact_number=self.cleaned_data['driver_contact'],
                image=self.cleaned_data['driver_image']
            )
        return bus

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customers
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']

class SafetyNotificationReportForm(forms.ModelForm):
    class Meta:
        model = SafetyNotificationReport
        fields = [
            'agent', 'report_title', 'incident_datetime', 'location', 'latitude', 'longitude',
            'bus', 'stop', 'incident_type', 'severity_level', 'description'
        ]

class TravelReportForm(forms.ModelForm):
    class Meta:
        model = TravelReport
        fields = ['departure', 'destination', 'travel_date', 'description']
        widgets = {
            'travel_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ReportPhotoForm(forms.ModelForm):
    class Meta:
        model = ReportPhoto
        fields = ['image', 'caption']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False