from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User, Profile


class Command(BaseCommand):
    help = 'Sync User first_name/last_name with Profile first_name/last_name'

    def add_arguments(self, parser):
        parser.add_argument(
            '--direction',
            type=str,
            default='profile_to_user',
            choices=['profile_to_user', 'user_to_profile'],
            help='Direction of sync: profile_to_user or user_to_profile'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        direction = options['direction']
        dry_run = options['dry_run']
        
        users_updated = 0
        profiles_updated = 0
        
        with transaction.atomic():
            users = User.objects.all()
            
            for user in users:
                try:
                    profile, created = Profile.objects.get_or_create(user=user)
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'Created profile for user: {user.email}')
                        )
                    
                    if direction == 'profile_to_user':
                        # Sync from Profile to User
                        update_needed = False
                        
                        if profile.first_name and profile.first_name != user.first_name:
                            if not dry_run:
                                user.first_name = profile.first_name
                            update_needed = True
                            self.stdout.write(
                                f'User {user.email}: first_name "{user.first_name}" -> "{profile.first_name}"'
                            )
                        
                        if profile.last_name and profile.last_name != user.last_name:
                            if not dry_run:
                                user.last_name = profile.last_name
                            update_needed = True
                            self.stdout.write(
                                f'User {user.email}: last_name "{user.last_name}" -> "{profile.last_name}"'
                            )
                        
                        if update_needed:
                            if not dry_run:
                                user.save()
                            users_updated += 1
                    
                    else:  # user_to_profile
                        # Sync from User to Profile
                        update_needed = False
                        
                        if user.first_name and user.first_name != profile.first_name:
                            if not dry_run:
                                profile.first_name = user.first_name
                            update_needed = True
                            self.stdout.write(
                                f'Profile {user.email}: first_name "{profile.first_name}" -> "{user.first_name}"'
                            )
                        
                        if user.last_name and user.last_name != profile.last_name:
                            if not dry_run:
                                profile.last_name = user.last_name
                            update_needed = True
                            self.stdout.write(
                                f'Profile {user.email}: last_name "{profile.last_name}" -> "{user.last_name}"'
                            )
                        
                        if update_needed:
                            if not dry_run:
                                profile.save()
                            profiles_updated += 1
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing user {user.email}: {str(e)}')
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN - No changes were made')
            )
        
        if direction == 'profile_to_user':
            self.stdout.write(
                self.style.SUCCESS(f'\nTotal users updated: {users_updated}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nTotal profiles updated: {profiles_updated}')
            )