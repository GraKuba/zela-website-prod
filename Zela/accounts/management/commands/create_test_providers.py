from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import ProviderProfile
from django.db import transaction
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test provider users with profiles'

    def handle(self, *args, **kwargs):
        providers_data = [
            {
                'username': 'maria_silva',
                'email': 'maria.silva@example.com',
                'first_name': 'Maria',
                'last_name': 'Silva',
                'phone_number': '+244923456789',
                'bio': 'Professional cleaner with 8 years of experience. Specializing in deep cleaning and organization. I take pride in leaving every home spotless!',
                'skills': ['Deep Cleaning', 'Organization', 'Laundry', 'Kitchen Specialist'],
                'jobs_completed': 342,
                'rating_average': 4.9,
                'rating_count': 287,
                'completion_rate': 98.5,
                'service_area': 'luanda-centro',
            },
            {
                'username': 'joao_santos',
                'email': 'joao.santos@example.com',
                'first_name': 'João',
                'last_name': 'Santos',
                'phone_number': '+244923456790',
                'bio': 'Experienced home service professional. Expert in indoor and outdoor cleaning. Available for same-day bookings!',
                'skills': ['Indoor Cleaning', 'Outdoor Services', 'Window Cleaning', 'Floor Care'],
                'jobs_completed': 189,
                'rating_average': 4.8,
                'rating_count': 156,
                'completion_rate': 97.2,
                'service_area': 'maianga',
            },
            {
                'username': 'ana_costa',
                'email': 'ana.costa@example.com',
                'first_name': 'Ana',
                'last_name': 'Costa',
                'phone_number': '+244923456791',
                'bio': 'Dedicated cleaning professional with attention to detail. Specialized in eco-friendly cleaning methods. Your satisfaction is my priority!',
                'skills': ['Eco-Friendly Cleaning', 'Pet-Friendly', 'Office Cleaning', 'Move-in/out Cleaning'],
                'jobs_completed': 267,
                'rating_average': 4.95,
                'rating_count': 234,
                'completion_rate': 99.1,
                'service_area': 'ingombota',
            },
            {
                'username': 'pedro_mendes',
                'email': 'pedro.mendes@example.com',
                'first_name': 'Pedro',
                'last_name': 'Mendes',
                'phone_number': '+244923456792',
                'bio': 'Reliable and efficient service provider. Expert in residential and commercial cleaning. Flexible scheduling available.',
                'skills': ['Commercial Cleaning', 'Residential Cleaning', 'Carpet Cleaning', 'Sanitization'],
                'jobs_completed': 145,
                'rating_average': 4.7,
                'rating_count': 128,
                'completion_rate': 96.8,
                'service_area': 'rangel',
            },
            {
                'username': 'fatima_neto',
                'email': 'fatima.neto@example.com',
                'first_name': 'Fátima',
                'last_name': 'Neto',
                'phone_number': '+244923456793',
                'bio': 'Experienced in all aspects of home cleaning and organization. Specialized in helping busy families maintain clean and organized homes.',
                'skills': ['Home Organization', 'Deep Cleaning', 'Laundry Services', 'Kitchen & Bathroom Expert'],
                'jobs_completed': 298,
                'rating_average': 4.85,
                'rating_count': 265,
                'completion_rate': 97.9,
                'service_area': 'cazenga',
            }
        ]

        with transaction.atomic():
            created_count = 0
            for provider_data in providers_data:
                # Check if user already exists
                if User.objects.filter(username=provider_data['username']).exists():
                    self.stdout.write(
                        self.style.WARNING(f"User {provider_data['username']} already exists, skipping...")
                    )
                    continue

                # Create user
                user = User.objects.create_user(
                    username=provider_data['username'],
                    email=provider_data['email'],
                    password='testpass123',
                    first_name=provider_data['first_name'],
                    last_name=provider_data['last_name']
                )
                # Update additional fields
                user.phone = provider_data['phone_number']
                user.role = 'provider'
                user.locale = 'pt-AO'
                user.save()

                # Create provider profile
                profile = ProviderProfile.objects.create(
                    user=user,
                    bio=provider_data['bio'],
                    skills=provider_data['skills'],
                    jobs_completed=provider_data['jobs_completed'],
                    rating_average=provider_data['rating_average'],
                    rating_count=provider_data['rating_count'],
                    completion_rate=provider_data['completion_rate'],
                    service_area=provider_data['service_area'],
                    is_approved=True,  # Auto-approve for testing
                    is_available=True,
                    accepts_same_day=random.choice([True, False]),
                    # Set some default working hours
                    working_hours={
                        'monday': {'enabled': True, 'start': '07:00', 'end': '18:00'},
                        'tuesday': {'enabled': True, 'start': '07:00', 'end': '18:00'},
                        'wednesday': {'enabled': True, 'start': '07:00', 'end': '18:00'},
                        'thursday': {'enabled': True, 'start': '07:00', 'end': '18:00'},
                        'friday': {'enabled': True, 'start': '07:00', 'end': '18:00'},
                        'saturday': {'enabled': True, 'start': '08:00', 'end': '16:00'},
                        'sunday': {'enabled': False, 'start': '09:00', 'end': '14:00'},
                    },
                    service_areas=[
                        {'name': 'Luanda Centro', 'enabled': True, 'surcharge': 0, 'color': '#10b981'},
                        {'name': 'Maianga', 'enabled': True, 'surcharge': 0, 'color': '#10b981'},
                        {'name': 'Ingombota', 'enabled': True, 'surcharge': 5, 'color': '#f59e0b'},
                        {'name': 'Rangel', 'enabled': True, 'surcharge': 10, 'color': '#f59e0b'},
                    ],
                    max_travel_distance=random.choice([15, 20, 25, 30]),
                    preferred_radius=random.choice([5, 10, 15]),
                    avoid_tolls=random.choice([True, False]),
                )

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created provider: {user.get_full_name()} ({user.username})"
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully created {created_count} provider users!"
                )
            )