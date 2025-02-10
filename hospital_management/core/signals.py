# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Patient, PatientHistory, User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=Patient)
def create_patient_history(sender, instance, created, **kwargs):
    if not created:
        PatientHistory.objects.create(
            patient=instance,
            changed_by=instance.updated_by,
            change_date=instance.updated_at,
            changes=instance.get_changes()
        )

@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)