# Generated by Django 5.1.5 on 2025-03-24 18:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_user_email_verified"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="doctor",
            name="license_number",
        ),
        migrations.RemoveField(
            model_name="doctor",
            name="qualification",
        ),
        migrations.RemoveField(
            model_name="patient",
            name="address",
        ),
        migrations.RemoveField(
            model_name="patient",
            name="emergency_contact",
        ),
        migrations.RemoveField(
            model_name="patient",
            name="emergency_phone",
        ),
        migrations.RemoveField(
            model_name="patient",
            name="phone",
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("phone_number", models.CharField(blank=True, max_length=20)),
                ("address", models.TextField(blank=True)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("country", models.CharField(blank=True, max_length=100)),
                (
                    "profile_picture",
                    models.ImageField(blank=True, upload_to="profile_pics/"),
                ),
                ("bio", models.TextField(blank=True)),
                ("emergency_contact", models.CharField(blank=True, max_length=100)),
                ("emergency_phone", models.CharField(blank=True, max_length=15)),
                ("license_number", models.CharField(blank=True, max_length=50)),
                ("qualifications", models.TextField(blank=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
