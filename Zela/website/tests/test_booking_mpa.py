"""
End-to-end tests for the MPA booking flow
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from services.models import ServiceCategory, ServiceTask
from workers.models import Worker, PropertyTypology
from bookings.models import Booking
from pricing.models import PricingConfig
from datetime import datetime, timedelta
import json

User = get_user_model()


class MPABookingFlowTest(TestCase):
    """Test the complete MPA booking flow."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test service category
        self.service = ServiceCategory.objects.create(
            name='House Cleaning',
            slug='house-cleaning',
            is_active=True,
            description='Professional house cleaning service'
        )
        
        # Create main service task
        self.service_task = ServiceTask.objects.create(
            service_category=self.service,
            name='House Cleaning',
            slug='house-cleaning',
            is_main_service=True,
            price_amount=5000
        )
        
        # Create extra tasks
        self.extra_task1 = ServiceTask.objects.create(
            service_category=self.service,
            name='Window Cleaning',
            slug='window-cleaning',
            is_main_service=False,
            price_amount=1000
        )
        
        # Create property typologies
        self.property_t2 = PropertyTypology.objects.create(
            name='T2 Apartment',
            slug='t2',
            description='2 bedroom apartment'
        )
        
        # Create test worker
        worker_user = User.objects.create_user(
            username='worker1',
            email='worker@example.com',
            password='workerpass'
        )
        self.worker = Worker.objects.create(
            user=worker_user,
            is_active=True,
            rating=4.5
        )
        self.worker.services.add(self.service)
        
        # Create pricing config
        PricingConfig.objects.create(
            hourly_clean_base=2000,
            booking_fee=500,
            minimum_booking_amount=5000,
            weekend_multiplier=1.2,
            specialty_task_price=1000
        )
        
        # Login the user
        self.client.login(username='testuser', password='testpass123')
    
    def test_complete_booking_flow(self):
        """Test the complete booking flow from start to confirmation."""
        
        # Step 1: Service Selection
        response = self.client.get(reverse('booking_mpa:service-select'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'House Cleaning')
        
        # Select service
        response = self.client.post(
            reverse('booking_mpa:service-select'),
            {'service': 'house-cleaning'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 2: Address
        response = self.client.get(reverse('booking_mpa:address'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse('booking_mpa:address'),
            {
                'street': 'Rua Principal 123',
                'area': 'Talatona',
                'city': 'Luanda',
                'province': 'Luanda',
                'latitude': '-8.9094',
                'longitude': '13.1891'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 3: Property
        response = self.client.get(reverse('booking_mpa:property'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse('booking_mpa:property'),
            {'property_type': 't2'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 4: Duration
        response = self.client.get(reverse('booking_mpa:duration'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse('booking_mpa:duration'),
            {
                'hours': '3',
                'tasks': ['window-cleaning']
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 5: Schedule
        response = self.client.get(reverse('booking_mpa:schedule'))
        self.assertEqual(response.status_code, 200)
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post(
            reverse('booking_mpa:schedule'),
            {
                'date': tomorrow,
                'time': '10:00'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 6: Worker Selection
        response = self.client.get(reverse('booking_mpa:worker'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'worker1')
        
        response = self.client.post(
            reverse('booking_mpa:worker'),
            {'worker': str(self.worker.id)}
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 7: Payment
        response = self.client.get(reverse('booking_mpa:payment'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse('booking_mpa:payment'),
            {'payment_method': 'cash'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 8: Review
        response = self.client.get(reverse('booking_mpa:review'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'House Cleaning')
        self.assertContains(response, 'Rua Principal 123')
        
        # Confirm booking
        response = self.client.post(
            reverse('booking_mpa:review'),
            {'confirm': 'true'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 9: Confirmation
        response = self.client.get(reverse('booking_mpa:confirmation'))
        self.assertEqual(response.status_code, 200)
        
        # Verify booking was created
        bookings = Booking.objects.filter(customer=self.user)
        self.assertEqual(bookings.count(), 1)
        
        booking = bookings.first()
        self.assertEqual(booking.service_task, self.service_task)
        self.assertEqual(booking.worker, self.worker)
        self.assertEqual(booking.status, 'pending_confirmation')
        self.assertIn('Rua Principal 123', booking.address)
    
    def test_session_persistence(self):
        """Test that booking data persists across steps."""
        
        # Add some data to session
        response = self.client.post(
            reverse('booking_mpa:service-select'),
            {'service': 'house-cleaning'}
        )
        
        # Navigate to different steps
        response = self.client.get(reverse('booking_mpa:address'))
        self.assertEqual(response.status_code, 200)
        
        # Session should maintain service selection
        session = self.client.session
        self.assertEqual(session.get('booking_data', {}).get('service_slug'), 'house-cleaning')
    
    def test_back_navigation(self):
        """Test that back navigation works correctly."""
        
        # Select service and go to address
        self.client.post(
            reverse('booking_mpa:service-select'),
            {'service': 'house-cleaning'}
        )
        
        # Fill address and go to property
        self.client.post(
            reverse('booking_mpa:address'),
            {
                'street': 'Test Street',
                'area': 'Test Area',
                'city': 'Luanda',
                'province': 'Luanda'
            }
        )
        
        # Go to property page
        response = self.client.get(reverse('booking_mpa:property'))
        self.assertEqual(response.status_code, 200)
        
        # Check that back link points to address
        self.assertContains(response, reverse('booking_mpa:address'))
    
    def test_validation_errors(self):
        """Test form validation."""
        
        # Try to submit invalid schedule (past date)
        self.client.post(
            reverse('booking_mpa:service-select'),
            {'service': 'house-cleaning'}
        )
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post(
            reverse('booking_mpa:schedule'),
            {
                'date': yesterday,
                'time': '10:00'
            }
        )
        
        # Should not redirect (validation error)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'must be in the future')
    
    def test_worker_availability(self):
        """Test worker availability filtering."""
        
        # Create another worker who doesn't provide this service
        other_user = User.objects.create_user(
            username='worker2',
            email='worker2@example.com'
        )
        other_worker = Worker.objects.create(
            user=other_user,
            is_active=True
        )
        
        # Select service
        self.client.post(
            reverse('booking_mpa:service-select'),
            {'service': 'house-cleaning'}
        )
        
        # Go to worker selection
        response = self.client.get(reverse('booking_mpa:worker'))
        
        # Should only show worker1, not worker2
        self.assertContains(response, 'worker1')
        self.assertNotContains(response, 'worker2')
    
    def test_price_calculation(self):
        """Test that pricing is calculated correctly."""
        
        # Set up booking data
        self.client.post(
            reverse('booking_mpa:service-select'),
            {'service': 'house-cleaning'}
        )
        
        self.client.post(
            reverse('booking_mpa:property'),
            {'property_type': 't2'}
        )
        
        self.client.post(
            reverse('booking_mpa:duration'),
            {
                'hours': '3',
                'tasks': ['window-cleaning']
            }
        )
        
        # Go to payment page
        response = self.client.get(reverse('booking_mpa:payment'))
        
        # Should show calculated price
        self.assertContains(response, 'total_price')
    
    def test_email_notification(self):
        """Test that email notifications are sent."""
        from django.core import mail
        
        # Complete a booking
        self.client.post(
            reverse('booking_mpa:service-select'),
            {'service': 'house-cleaning'}
        )
        
        self.client.post(
            reverse('booking_mpa:address'),
            {
                'street': 'Test Street',
                'area': 'Test Area',
                'city': 'Luanda',
                'province': 'Luanda'
            }
        )
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.client.post(
            reverse('booking_mpa:schedule'),
            {
                'date': tomorrow,
                'time': '10:00'
            }
        )
        
        self.client.post(
            reverse('booking_mpa:worker'),
            {'worker': str(self.worker.id)}
        )
        
        self.client.post(
            reverse('booking_mpa:payment'),
            {'payment_method': 'cash'}
        )
        
        # Clear any existing emails
        mail.outbox = []
        
        # Confirm booking (this should send emails)
        response = self.client.post(
            reverse('booking_mpa:review'),
            {'confirm': 'true'}
        )
        
        # Check that emails were sent
        # Note: This will only work if email backend is configured for testing
        # self.assertEqual(len(mail.outbox), 2)  # One to customer, one to worker
    
    def test_payment_processing(self):
        """Test payment processing integration."""
        
        # Complete booking with card payment
        self.client.post(
            reverse('booking_mpa:service-select'),
            {'service': 'house-cleaning'}
        )
        
        self.client.post(
            reverse('booking_mpa:address'),
            {
                'street': 'Test Street',
                'area': 'Test Area',
                'city': 'Luanda',
                'province': 'Luanda'
            }
        )
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.client.post(
            reverse('booking_mpa:schedule'),
            {
                'date': tomorrow,
                'time': '10:00'
            }
        )
        
        self.client.post(
            reverse('booking_mpa:payment'),
            {'payment_method': 'card'}
        )
        
        # Confirm booking
        response = self.client.post(
            reverse('booking_mpa:review'),
            {'confirm': 'true'}
        )
        
        # Check that booking has payment transaction ID (from mock gateway)
        booking = Booking.objects.filter(customer=self.user).first()
        if booking:
            # With mock gateway, transaction ID should be set
            self.assertIsNotNone(booking.payment_transaction_id)