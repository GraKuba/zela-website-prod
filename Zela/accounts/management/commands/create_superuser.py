from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser for deployment'

    def handle(self, *args, **options):
        email = 'admin@zela.com'
        password = 'Zela123!'
        
        try:
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'Superuser with email {email} already exists.')
                )
                return
            
            user = User.objects.create_superuser(
                email=email,
                password=password,
                role='admin'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Superuser created successfully with email: {email}')
            )
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )