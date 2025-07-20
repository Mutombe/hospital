from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
    
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('ADMIN', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='PATIENT')
    # is_doctor and is_patient can be derived from the role, so they might be redundant
    # but keeping them as per your original model
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    # Resolve conflicts by adding custom related_names
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user'
    )

    # Assuming token_blacklist is in use, keeping this
    token_relationships = models.ManyToManyField(
        'token_blacklist.OutstandingToken',
        related_name='user_tokens',
        blank=True
    )

    profile_complete = models.BooleanField(default=False)
    
    def update_profile_complete(self):
        """Update profile completion status"""
        try:
            profile = self.profile
            required_fields = {
                'all': ['phone_number', 'address', 'city', 'country'],
                'PATIENT': ['emergency_contact', 'emergency_phone'],
                'DOCTOR': ['license_number', 'qualifications']
            }
            
            # Check common fields
            for field in required_fields['all']:
                if not getattr(profile, field):
                    return False
            
            # Check role-specific fields
            if self.role == 'PATIENT':
                for field in required_fields['PATIENT']:
                    if not getattr(profile, field):
                        return False
                        
            elif self.role == 'DOCTOR':
                for field in required_fields['DOCTOR']:
                    if not getattr(profile, field):
                        return False
            
            return True
        except Profile.DoesNotExist:
            return False

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.role == 'DOCTOR':
            self.is_doctor = True
            self.is_patient = False
        elif self.role == 'PATIENT':
            self.is_doctor = False
            self.is_patient = True
        else:
            self.is_doctor = False
            self.is_patient = False
        super().save(*args, **kwargs)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default='Zimbabwe')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True)

    # Fields to track profile completion
    # We will derive this based on other fields being filled
    # For simplicity, we can just use the existence of key fields
    # Example: For a patient, if phone_number, address, and emergency_contact are filled.
    # For a doctor, if phone_number, address, license_number, and qualifications are filled.
    # We will calculate this on the fly or through a method.

    # Patient-specific proxy fields
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)

    # Doctor-specific proxy fields
    license_number = models.CharField(max_length=50, blank=True)
    qualifications = models.TextField(blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    experience_years = models.IntegerField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def is_complete(self):
        """
        Checks if the profile is complete based on the user's role.
        You can customize what fields are considered 'required' for completion.
        """
        # Common required fields for both
        common_required = all([
            self.phone_number,
            self.address,
            self.city,
            self.country,
            self.bio,
        ])

        if self.user.role == 'PATIENT':
            return common_required and all([
                self.date_of_birth,
                self.gender,
                self.blood_type,
                self.emergency_contact,
                self.emergency_phone,
            ])
        elif self.user.role == 'DOCTOR':
            return common_required and all([
                self.license_number,
                self.qualifications,
                self.specialty,
                self.experience_years is not None, # Check for presence, 0 is valid
                self.consultation_fee is not None, # Check for presence, 0.00 is valid
            ])
        return common_required # For ADMIN or other roles, just common fields

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]
    
    BLOOD_TYPES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-')
    ]

    mrn = models.CharField(max_length=10, unique=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(default=timezone.now)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="O")
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, default='0+')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


    def get_changes(self):
        return {
            'mrn': self.mrn,
            'date_of_birth': self.date_of_birth,
            'gender': self.gender,
            'blood_type': self.blood_type,
        }

    def __str__(self):
        return f"{self.user.username} {self.gender} {self.blood_type}"

class VitalSigns(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    temperature = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(35.0), MaxValueValidator(42.0)]
    )
    blood_pressure_systolic = models.IntegerField()
    blood_pressure_diastolic = models.IntegerField()
    heart_rate = models.IntegerField()
    respiratory_rate = models.IntegerField()
    oxygen_saturation = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.temperature}°C, BP: {self.blood_pressure_systolic}/{self.blood_pressure_diastolic}, HR: {self.heart_rate}, RR: {self.respiratory_rate}, O2: {self.oxygen_saturation}%"

class Diagnosis(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    icd_code = models.CharField(max_length=10)
    description = models.TextField()
    diagnosed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    diagnosed_date = models.DateField()
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.icd_code} - {self.description}"

class Medication(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    prescribed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=255)  # The affected resource/endpoint
    details = models.TextField(null=True, blank=True)  # Additional details about the action
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user} - {self.action} - {self.resource}"

class PatientHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_date = models.DateTimeField(auto_now_add=True)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True)
    new_value = models.TextField(null=True)
    
    class Meta:
        ordering = ['-change_date']

    def display_change(self):
        if self.old_value and self.new_value:
            return f"Changed from '{self.old_value}' to '{self.new_value}'"
        elif self.new_value:
            return f"Set to '{self.new_value}'"
        return "No change recorded"
    
    def __str__(self):
        return f"{self.patient.user.username} - {self.field_name} at {self.change_date}"

class Specialty(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True)
    experience_years = models.IntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    available_for_appointments = models.BooleanField(default=True)
    max_patients_per_day = models.IntegerField(default=20)
    
    def is_available(self, date, time):
        # Check if doctor is on leave
        leave_exists = DoctorLeave.objects.filter(
            doctor=self,
            start_date__lte=date,
            end_date__gte=date,
            status='APPROVED'
        ).exists()
        
        if leave_exists:
            return False
            
        # Check schedule
        day_of_week = date.weekday()
        schedule = DoctorSchedule.objects.filter(
            doctor=self,
            day_of_week=day_of_week,
            start_time__lte=time,
            end_time__gte=time,
            is_available=True
        ).exists()
        
        if not schedule:
            return False
            
        # Check number of appointments for that day
        appointments_count = Appointment.objects.filter(
            doctor=self,
            date=date,
            status='PENDING'
        ).count()
        
        return appointments_count < self.max_patients_per_day
    
    def __str__(self):
        return f"{self.user.username} {self.specialty}"

class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'day_of_week', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.doctor.user.username} - {self.day_of_week}"

class DoctorLeave(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(default="Emergency")
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )

    def __str__(self):
        return f"{self.doctor.user.username} - {self.start_date} to {self.end_date}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show')
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField(default="General Checkup")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        
    def save(self, *args, **kwargs):
        if not self.pk:  # New appointment
            if not self.doctor.is_available(self.appointment_date, self.appointment_time):
                raise ValueError("Doctor is not available at this time")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.user.username} - {self.doctor.user.username} {self.appointment_date} {self.appointment_time}"

class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='medical_records')
    diagnosis = models.TextField()
    prescription = models.TextField()
    notes = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Medical Record for {self.patient.user.username}"
