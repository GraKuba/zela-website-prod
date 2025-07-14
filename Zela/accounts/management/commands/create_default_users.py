from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser and provider user for deployment'

    def handle(self, *args, **options):
        # Create superuser
        admin_email = 'admin@zela.com'
        admin_password = 'Zela123!'
        
        try:
            if User.objects.filter(email=admin_email).exists() or User.objects.filter(username=admin_email).exists():
                self.stdout.write(
                    self.style.WARNING(f'Superuser with email {admin_email} already exists.')
                )
            else:
                user = User.objects.create_superuser(
                    username=admin_email,
                    email=admin_email,
                    password=admin_password,
                    role='admin',
                    is_staff=True,
                    is_superuser=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Superuser created successfully with email: {admin_email}')
                )
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error creating superuser: {e}')
            )
        
        # Create provider user
        provider_email = 'provider@zela.com'
        provider_password = 'Zela123!'
        
        try:
            if User.objects.filter(email=provider_email).exists() or User.objects.filter(username=provider_email).exists():
                self.stdout.write(
                    self.style.WARNING(f'Provider user with email {provider_email} already exists.')
                )
            else:
                provider_user = User.objects.create_user(
                    username=provider_email,
                    email=provider_email,
                    password=provider_password,
                    role='provider'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Provider user created successfully with email: {provider_email}')
                )
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating provider user: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error creating provider user: {e}')
            )