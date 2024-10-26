from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from .models import SafetyNotificationReport, BusBooking
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

def send_sms_twilio(phone_number, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"SMS sent successfully to {phone_number}")
        return True
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {str(e)}")
        return False

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import SafetyNotificationReport, BusBooking

def send_safety_notification(report_id):
    print(f"Starting send_safety_notification for report ID: {report_id}")
    try:
        report = SafetyNotificationReport.objects.get(report_id=report_id)
        print(f"Report found: Bus ID: {report.bus.bus_id}, Stop: {report.stop}, Incident Date: {report.incident_datetime}")
    except SafetyNotificationReport.DoesNotExist:
        print(f"Report with ID {report_id} not found")
        return 0

    incident_date = report.incident_datetime.date()
    bus = report.bus
    print(f"Bus schedule date: {bus.date}, Incident date: {incident_date}")

    if bus.date != incident_date:
        print(f"No scheduled trip for this bus on the incident date. Bus schedule date: {bus.date}, Incident date: {incident_date}")
        return 0

    affected_bookings = BusBooking.objects.filter(
        bus=bus,
        payment_status='Paid'
    )
    print(f"Number of affected bookings: {affected_bookings.count()}")

    all_bookings = BusBooking.objects.filter(bus=bus)
    print(f"Total bookings for this bus: {all_bookings.count()}")
    for booking in all_bookings:
        print(f"Booking ID: {booking.booking_id}, Bus Date: {bus.date}, Booking Date: {booking.booking_date}, Customer: {booking.customer.email}, Payment Status: {booking.payment_status}")

    affected_customers = [booking.customer for booking in affected_bookings]
    print(f"Number of affected customers: {len(affected_customers)}")

    if not affected_customers:
        print("No affected customers found. Exiting function.")
        return 0

    subject = f"Safety Alert: {report.severity_level} Incident"
    
    # Render the email message using the template
    email_context = {
        'severity_level': report.severity_level,
        'location': report.location,
        'description': report.description,
    }
    html_content = render_to_string('emails/safety_alert_email.html', email_context)
    text_content = strip_tags(html_content)  # Create a plain-text version of the HTML
    
    from_email = settings.DEFAULT_FROM_EMAIL

    email_recipients = []
    sms_recipients = []

    for customer in affected_customers:
        if customer.email:
            email_recipients.append(customer.email)
        if customer.phone:
            sms_recipients.append(customer.phone)

    print(f"Email recipients: {email_recipients}")
    print(f"SMS recipients: {sms_recipients}")

    email_sent = 0
    if email_recipients:
        try:
            for recipient in email_recipients:
                msg = EmailMultiAlternatives(subject, text_content, from_email, [recipient])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                email_sent += 1
            print(f"Emails sent to {email_sent} recipients")
        except Exception as e:
            print(f"Error sending emails: {str(e)}")

    sms_sent = 0
    sms_message = f"Safety Alert: {report.severity_level} incident at {report.location}. This may affect your journey. Check your email for details."
    for phone_number in sms_recipients:
        if send_sms_twilio(phone_number, sms_message):
            sms_sent += 1

    print(f"SMS sent to {sms_sent} recipients")
    print(f"Total emails sent: {email_sent}")

    total_notifications = email_sent + sms_sent
    print(f"Total notifications sent: {total_notifications}")
    return total_notifications