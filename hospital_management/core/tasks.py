# tasks.py
from celery import shared_task
from django.core.mail import send_mail
from datetime import datetime, timedelta
from .models import Appointment

@shared_task
def send_appointment_reminder():
    tomorrow = datetime.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        appointment_date=tomorrow,
        status='CONFIRMED'
    )
    
    for appointment in appointments:
        send_mail(
            'Appointment Reminder',
            f'Dear {appointment.patient.user.get_full_name()},\n\n'
            f'This is a reminder for your appointment with Dr. {appointment.doctor.user.get_full_name()} '
            f'tomorrow at {appointment.appointment_time}.\n\n'
            f'Please arrive 15 minutes before your scheduled time.',
            'from@example.com',
            [appointment.patient.user.email],
            fail_silently=False,
        )

@shared_task
def send_appointment_confirmation(appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    send_mail(
        'Appointment Confirmation',
        f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} '
        f'has been confirmed for {appointment.appointment_date} at {appointment.appointment_time}.',
        'from@example.com',
        [appointment.patient.user.email],
        fail_silently=False,
    )