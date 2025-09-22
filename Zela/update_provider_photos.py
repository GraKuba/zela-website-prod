#!/usr/bin/env python3
import os
import sys

# Setup Django environment
sys.path.insert(0, '/Users/kubagrabarczyk/Desktop/Freelance/ZELA/zela-website/Zela')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Zela.settings')

import django
django.setup()

from django.core.files import File

from accounts.models import User, Profile

# Photo mapping - using available photos for the requested providers
photo_mapping = {
    'Maria Silva': 'marisa-gaspar-1.jpeg',
    'João Santos': 'milton-tomas-1.jpeg', 
    'Ana Costa': 'madalena-rodrigues-1.jpeg',
    'Pedro Mendes': 'milton-tomas-2.jpeg',
    'Fátima Neto': 'vanuza-faustino-1.jpeg'
}

photo_dir = '/Users/kubagrabarczyk/Desktop/Freelance/ZELA/zela-website/Zela/website/static/zela-workers-new-photos'

def update_provider_photos():
    updated_count = 0
    not_found = []
    
    for full_name, photo_filename in photo_mapping.items():
        first_name, last_name = full_name.split(' ', 1)
        
        # Try to find the user
        try:
            user = User.objects.get(first_name=first_name, last_name=last_name)
            
            # Get or create profile
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Open and assign the photo
            photo_path = os.path.join(photo_dir, photo_filename)
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo_file:
                    profile.profile_picture.save(photo_filename, File(photo_file), save=True)
                    print(f"✓ Updated {full_name} with photo {photo_filename}")
                    updated_count += 1
            else:
                print(f"✗ Photo file not found: {photo_path}")
                
        except User.DoesNotExist:
            not_found.append(full_name)
            print(f"✗ User not found: {full_name}")
        except User.MultipleObjectsReturned:
            print(f"✗ Multiple users found with name: {full_name}")
        except Exception as e:
            print(f"✗ Error updating {full_name}: {str(e)}")
    
    print(f"\n--- Summary ---")
    print(f"Successfully updated: {updated_count} providers")
    if not_found:
        print(f"Users not found: {', '.join(not_found)}")
        print("\nLet's check what users exist in the database...")
        
        # List all users with provider role
        providers = User.objects.filter(role='provider')[:20]
        if providers:
            print(f"\nExisting providers in database:")
            for p in providers:
                print(f"  - {p.first_name} {p.last_name} ({p.username})")

if __name__ == '__main__':
    update_provider_photos()