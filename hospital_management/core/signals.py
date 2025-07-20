from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Patient, PatientHistory, Profile
from django.utils import timezone

# signals.py
@receiver(post_save, sender=Profile)
def update_profile_complete(sender, instance, **kwargs):
    """Update profile completion status when profile changes"""
    user = instance.user
    is_complete = user.update_profile_complete()
    
    if user.profile_complete != is_complete:
        user.profile_complete = is_complete
        user.save(update_fields=['profile_complete'])

@receiver(pre_save, sender=Patient)
def capture_pre_save_state(sender, instance, **kwargs):
    """Store pre-save state of Patient instance for later comparison"""
    try:
        instance._pre_save_instance = Patient.objects.get(pk=instance.pk)
    except Patient.DoesNotExist:
        instance._pre_save_instance = None

@receiver(post_save, sender=Patient)
def log_patient_history(sender, instance, created, **kwargs):
    """Create PatientHistory entries for changed fields"""
    # Fields to track for history
    tracked_fields = ['mrn', 'date_of_birth', 'gender', 'blood_type']
    
    if created:
        # Log all fields during creation
        for field in tracked_fields:
            new_value = getattr(instance, field)
            PatientHistory.objects.create(
                patient=instance,
                changed_by=instance.user,
                field_name=field,
                old_value=None,
                new_value=str(new_value) if new_value is not None else None
            )
    else:
        # Log only changed fields during update
        old_instance = getattr(instance, '_pre_save_instance', None)
        if not old_instance:
            return

        for field in tracked_fields:
            old_value = getattr(old_instance, field)
            new_value = getattr(instance, field)
            
            if old_value != new_value:
                PatientHistory.objects.create(
                    patient=instance,
                    changed_by=instance.user,
                    field_name=field,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(new_value) if new_value is not None else None
                )