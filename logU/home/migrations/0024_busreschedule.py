# Generated by Django 5.0.6 on 2024-09-28 18:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0023_alter_bus_bus_number_busimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusReschedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_departure_location', models.CharField(max_length=100)),
                ('old_destination_location', models.CharField(max_length=100)),
                ('old_departure_date', models.DateField()),
                ('old_departure_time', models.TimeField()),
                ('old_arrival_date', models.DateField()),
                ('old_arrival_time', models.TimeField()),
                ('old_stops', models.TextField()),
                ('new_departure_location', models.CharField(max_length=100)),
                ('new_destination_location', models.CharField(max_length=100)),
                ('new_departure_date', models.DateField()),
                ('new_departure_time', models.TimeField()),
                ('new_arrival_date', models.DateField()),
                ('new_arrival_time', models.TimeField()),
                ('new_stops', models.TextField()),
                ('rescheduled_at', models.DateTimeField(auto_now_add=True)),
                ('bus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reschedules', to='home.bus')),
                ('moderator', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bus_reschedules', to='home.moderator')),
            ],
        ),
    ]
