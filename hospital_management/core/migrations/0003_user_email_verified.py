# Generated by Django 5.1.5 on 2025-02-18 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_user_token_relationships"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
    ]
