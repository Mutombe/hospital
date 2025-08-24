# Backend: tasks.py (Celery tasks for notifications)
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

@shared_task
def send_appointment_confirmation(appointment_id):
    from .models import Appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        patient_email = appointment.patient.user.email
        
        subject = 'Appointment Request Received'
        message = f'''
        Dear {appointment.patient.user.first_name},
        
        Your appointment request with Dr. {appointment.doctor.user.last_name} 
        on {appointment.appointment_date} at {appointment.appointment_time} has been received.
        
        You will be notified once the doctor confirms your appointment.
        
        Reason: {appointment.reason}
        
        Thank you,
        Healthcare Team
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [patient_email],
            fail_silently=False,
        )
    except Appointment.DoesNotExist:
        pass

@shared_task
def send_appointment_notification(appointment_id):
    from .models import Appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        doctor_email = appointment.doctor.user.email
        
        subject = 'New Appointment Request'
        message = f'''
        Dear Dr. {appointment.doctor.user.last_name},
        
        You have a new appointment request from {appointment.patient.user.first_name} {appointment.patient.user.last_name}.
        
        Date: {appointment.appointment_date}
        Time: {appointment.appointment_time}
        Reason: {appointment.reason}
        
        Please log in to the system to accept or reject this appointment.
        
        Thank you,
        Healthcare Team
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [doctor_email],
            fail_silently=False,
        )
    except Appointment.DoesNotExist:
        pass

@shared_task
def send_appointment_status_update(appointment_id, status, note=None):
    from .models import Appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        patient_email = appointment.patient.user.email
        
        if status == "accepted":
            subject = 'Appointment Confirmed'
            message = f'''
            Dear {appointment.patient.user.first_name},
            
            Your appointment with Dr. {appointment.doctor.user.last_name} 
            on {appointment.appointment_date} at {appointment.appointment_time} has been confirmed.
            
            Please arrive 15 minutes before your scheduled time.
            
            Reason: {appointment.reason}
            
            Thank you,
            Healthcare Team
            '''
        else:
            subject = 'Appointment Rejected'
            message = f'''
            Dear {appointment.patient.user.first_name},
            
            Unfortunately, your appointment with Dr. {appointment.doctor.user.last_name} 
            on {appointment.appointment_date} at {appointment.appointment_time} has been rejected.
            
            Reason: {note}
            
            Please contact us to reschedule or choose another doctor.
            
            Thank you,
            Healthcare Team
            '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [patient_email],
            fail_silently=False,
        )
    except Appointment.DoesNotExist:
        pass

@shared_task
def send_appointment_reminders():
    from .models import Appointment
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    appointments = Appointment.objects.filter(
        appointment_date=tomorrow,
        status='CONFIRMED'
    )
    
    for appointment in appointments:
        patient_email = appointment.patient.user.email
        subject = 'Appointment Reminder'
        message = f'''
        Dear {appointment.patient.user.first_name},
        
        This is a reminder for your appointment with Dr. {appointment.doctor.user.last_name} 
        tomorrow ({appointment.appointment_date}) at {appointment.appointment_time}.
        
        Please arrive 15 minutes before your scheduled time.
        
        Reason: {appointment.reason}
        
        Thank you,
        Healthcare Team
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [patient_email],
            fail_silently=False,
        )