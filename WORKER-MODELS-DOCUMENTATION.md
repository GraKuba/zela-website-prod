# Zela Worker Models Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Model Structure](#model-structure)
4. [Pricing Models](#pricing-models)
5. [Service Configuration](#service-configuration)
6. [Usage Examples](#usage-examples)
7. [Admin Interface](#admin-interface)
8. [Migration Guide](#migration-guide)

## Overview

The Zela Worker Models system provides a flexible, extensible architecture for managing different types of service workers with their unique requirements, pricing models, and capabilities. The system supports various pricing strategies including hourly rates, fixed prices, per-unit pricing, package deals, and property-based pricing.

## Architecture

### Core Components

```
workers/
├── models.py           # Worker models and service packages
├── admin.py           # Admin interface configuration
└── migrations/        # Database migrations

services/
├── models.py          # Enhanced with pricing models
└── admin.py          # Service administration

bookings/
├── models.py         # Enhanced with worker relationships
└── admin.py         # Booking management
```

### Model Hierarchy

```
Worker (Base Model)
├── CleaningWorker
├── ElectricianWorker
├── ACTechnicianWorker
├── PestControlWorker
├── DogTrainerWorker
├── HandymanWorker
├── GardenerWorker
└── PlacementWorker
```

## Model Structure

### Base Worker Model

The `Worker` model contains all common fields shared across worker types:

```python
# Core Fields
- user: OneToOne relationship with User model
- bio: Text description
- years_experience: Integer
- languages: JSON list ['pt', 'en', 'fr']

# Verification
- status: pending/approved/suspended/inactive
- is_verified: Boolean for KYC
- background_check: Boolean
- id_document: File upload
- proof_of_address: File upload

# Performance Metrics
- rating_average: Decimal (0-5)
- rating_count: Integer
- jobs_completed: Integer
- jobs_cancelled: Integer
- completion_rate: Percentage

# Financial
- total_earnings: Decimal (AOA)
- current_balance: Decimal (AOA)

# Availability
- is_available: Boolean
- accepts_emergency: Boolean
- accepts_same_day: Boolean
- service_areas: JSON list
- max_travel_distance: Integer (km)
- working_hours: JSON schedule
```

### Property Typology

Defines property types for pricing calculations:

```python
PropertyTypology:
- T1: 1 Bedroom
- T2: 2 Bedrooms
- T3: 3 Bedrooms
- T4+: 4+ Bedrooms
```

### Service-Specific Workers

#### ElectricianWorker
```python
# Specific Fields
- license_number: String
- license_expiry: Date
- voltage_certifications: JSON ['low', 'medium', 'high']
- specializations: JSON ['residential', 'commercial', 'industrial']
- minimum_hours: Integer (default: 2)
- typology_rates: JSON {
    'T1': 8000,
    'T2': 9000,
    'T3': 10000,
    'T4+': 12000
  }
- emergency_surcharge: Decimal (percentage)
```

#### ACTechnicianWorker
```python
# Specific Fields
- hvac_certification: String
- refrigerant_license: String
- brands_serviced: JSON ['LG', 'Samsung', 'Daikin']
- service_types: JSON ['installation', 'repair', 'maintenance']
- unit_pricing: JSON {
    '1': 16000,
    '2-3': 14400,  # -10% each
    '4-5': 13600,  # -15% each
    '6+': 12800    # -20% each
  }
- has_diagnostic_tools: Boolean
```

#### PestControlWorker
```python
# Specific Fields
- pest_control_license: String
- chemical_certification: String
- service_types: general/deratization/both
- chemicals_used: JSON list
- eco_friendly_options: Boolean
- typology_pricing: JSON {
    'general': {
        'T1': 10000,
        'T2': 20000,
        'T3': 35000,
        'T4+': 40000
    },
    'deratization': {
        'T1': 18000,
        'T2': 28000,
        'T3': 38000,
        'T4+': 50000
    }
  }
```

#### DogTrainerWorker
```python
# Specific Fields
- certifications: JSON ['CCPDT', 'IAABC']
- training_methods: positive/balanced/clicker/behavior
- specializations: JSON ['puppy', 'aggression', 'obedience']
- breed_experience: JSON list
- max_dogs_per_session: Integer
- offers_group_classes: Boolean
- package_offerings: JSON {
    'evaluation': {'sessions': 1, 'price': 15000},
    'single': {'sessions': 1, 'price': 20000},
    'pack_5': {'sessions': 5, 'price': 90000},
    'pack_10': {'sessions': 10, 'price': 160000}
  }
```

### Service Package Model

For credit-based services (like dog training):

```python
ServicePackage:
- customer: ForeignKey to User
- worker: ForeignKey to Worker
- package_name: String (e.g., '5-Session Pack')
- package_type: String identifier
- total_credits: Integer
- used_credits: Integer
- amount_paid: Decimal
- status: active/depleted/expired/cancelled
- purchase_date: DateTime
- expiry_date: DateTime (optional)
```

## Pricing Models

### Available Pricing Models

```python
class PricingModel(TextChoices):
    FIXED = 'fixed'           # Fixed price
    HOURLY = 'hourly'         # Simple hourly rate
    HOURLY_MINIMUM = 'hourly_min'  # Hourly with minimum
    PER_UNIT = 'per_unit'     # Per unit with discounts
    PACKAGE = 'package'       # Pre-purchased packages
    TYPOLOGY_BASED = 'typology'    # Based on property type
```

### Service Configuration

#### ServiceCategory Enhancement
```python
ServiceCategory:
- worker_model_type: Links to specific worker class
- pricing_model: Default pricing for category
- booking_requirements: JSON {
    'minimum_hours': 2,
    'requires_property_type': true,
    'requires_unit_count': false
  }
```

#### ServiceTask Enhancement
```python
ServiceTask:
- pricing_model: Override category default
- pricing_config: JSON configuration
- skill_requirements: JSON list
- equipment_requirements: JSON list
- certification_requirements: JSON list
```

### Pricing Configuration Examples

#### Electrician (Hourly with Minimum + Typology)
```json
{
  "minimum_hours": 2,
  "typology_rates": {
    "T1": 8000,
    "T2": 9000,
    "T3": 10000,
    "T4+": 12000
  }
}
```

#### AC Repair (Per Unit with Volume Discounts)
```json
{
  "base_price": 16000,
  "volume_discounts": {
    "1": 0,
    "2-3": 10,
    "4-5": 15,
    "6+": 20
  }
}
```

#### Pest Control (Fixed by Typology)
```json
{
  "general": {
    "T1": 10000,
    "T2": 20000,
    "T3": 35000,
    "T4+": 40000
  },
  "deratization": {
    "T1": 18000,
    "T2": 28000,
    "T3": 38000,
    "T4+": 50000
  }
}
```

#### Dog Trainer (Package System)
```json
{
  "packages": [
    {"name": "Evaluation", "sessions": 1, "price": 15000},
    {"name": "Single", "sessions": 1, "price": 20000},
    {"name": "5-Pack", "sessions": 5, "price": 90000},
    {"name": "10-Pack", "sessions": 10, "price": 160000}
  ]
}
```

## Usage Examples

### Creating a New Electrician Worker

```python
from accounts.models import User
from workers.models import ElectricianWorker

# Create user account
user = User.objects.create_user(
    username='john_electrician',
    email='john@example.com',
    role='provider'
)

# Create electrician profile
electrician = ElectricianWorker.objects.create(
    user=user,
    bio="Licensed electrician with 10 years experience",
    years_experience=10,
    languages=['pt', 'en'],
    license_number='EL-12345',
    minimum_hours=2,
    typology_rates={
        'T1': 8000,
        'T2': 9000,
        'T3': 10000,
        'T4+': 12000
    },
    specializations=['residential', 'commercial'],
    voltage_certifications=['low', 'medium']
)
```

### Creating a Service with Pricing

```python
from services.models import ServiceCategory, ServiceTask, PricingModel

# Create category
category = ServiceCategory.objects.create(
    name='Electrical Services',
    slug='electrical-services',
    icon='bolt',
    worker_model_type='ElectricianWorker',
    pricing_model=PricingModel.HOURLY_MINIMUM,
    booking_requirements={
        'minimum_hours': 2,
        'requires_property_type': True
    }
)

# Create task
task = ServiceTask.objects.create(
    category=category,
    name='General Electrical Repair',
    price=8000,  # Base price
    pricing_config={
        'minimum_hours': 2,
        'typology_rates': {
            'T1': 8000,
            'T2': 9000,
            'T3': 10000,
            'T4+': 12000
        }
    },
    skill_requirements=['electrical_license'],
    duration_hours=2.0
)
```

### Creating a Booking with New System

```python
from bookings.models import Booking
from workers.models import PropertyTypology

# Get property type
property_type = PropertyTypology.objects.get(name='T2')

# Create booking
booking = Booking.objects.create(
    customer=customer_user,
    worker=electrician,  # ElectricianWorker instance
    service_task=task,
    property_typology=property_type,
    start_at=datetime.now(),
    end_at=datetime.now() + timedelta(hours=2),
    address='123 Main St',
    total_price=18000,  # 2 hours * 9000 (T2 rate)
    amount_prepaid=18000,  # Paid upfront for minimum
    amount_pending=0  # Will be calculated if exceeds minimum
)
```

### Using Service Packages

```python
from workers.models import ServicePackage

# Customer purchases a package
package = ServicePackage.objects.create(
    customer=customer_user,
    worker=dog_trainer,
    package_name='5-Session Pack',
    package_type='dog_training_5',
    total_credits=5,
    amount_paid=90000
)

# Use a credit for booking
booking = Booking.objects.create(
    customer=customer_user,
    worker=dog_trainer,
    service_task=dog_training_task,
    package_used=package,
    credits_consumed=1,
    # No payment required - using package
    total_price=0,
    amount_prepaid=0
)

# Deduct credit
package.use_credit(1)
```

## Admin Interface

### Accessing Admin

1. Navigate to `/admin/`
2. Login with superuser credentials

### Worker Management

**Workers > [Worker Type]**
- View all workers by type
- Filter by status, availability, verification
- Bulk actions:
  - Approve workers
  - Suspend workers
  - Mark available/unavailable
- View performance metrics
- Manage documents and verification

### Service Configuration

**Services > Service Categories**
- Configure worker model types
- Set default pricing models
- Define booking requirements

**Services > Service Tasks**
- Configure pricing details
- Set skill/equipment requirements
- Manage task availability

### Package Management

**Workers > Service Packages**
- View all packages
- Track credit usage
- Monitor expiration
- Manual credit adjustments

## Migration Guide

### From Old ProviderProfile to New Worker System

1. **Data Migration Steps**:
```python
# Migration script example
from accounts.models import ProviderProfile
from workers.models import CleaningWorker

for provider in ProviderProfile.objects.all():
    # Determine worker type based on skills
    if 'cleaning' in provider.skills:
        CleaningWorker.objects.create(
            user=provider.user,
            bio=provider.bio,
            # Map other fields...
            specializations=provider.skills,
            status='approved' if provider.is_approved else 'pending'
        )
```

2. **Update Bookings**:
```python
from bookings.models import Booking

for booking in Booking.objects.all():
    if booking.provider:
        # Find corresponding worker
        worker = Worker.objects.get(user=booking.provider)
        booking.worker = worker
        booking.save()
```

3. **Configure Services**:
- Update each ServiceCategory with `worker_model_type`
- Add `pricing_config` to ServiceTasks
- Set appropriate `pricing_model` for each category

## Best Practices

### 1. Worker Creation
- Always verify documents before approving
- Set appropriate service areas and travel distance
- Configure working hours accurately
- Ensure pricing configuration matches service requirements

### 2. Service Configuration
- Use category-level pricing models when consistent
- Override at task level only when necessary
- Keep pricing_config synchronized with worker capabilities
- Document special requirements clearly

### 3. Package Management
- Set appropriate expiration dates
- Monitor credit usage regularly
- Implement automatic expiration checks
- Consider package transfer policies

### 4. Booking Flow
- Validate worker availability before booking
- Check package credits before using
- Calculate final amounts accurately for hourly services
- Track payment states properly

## Troubleshooting

### Common Issues

**Issue**: Worker not appearing in booking options
- Check worker status (must be 'approved')
- Verify is_available = True
- Ensure worker type matches service category
- Check service areas coverage

**Issue**: Pricing calculation incorrect
- Verify pricing_config in ServiceTask
- Check property_typology is set for typology-based pricing
- Ensure unit_count is set for per-unit pricing
- Validate minimum hours for hourly services

**Issue**: Package credits not deducting
- Check package status (must be 'active')
- Verify expiry_date hasn't passed
- Ensure remaining_credits > 0
- Call package.use_credit() after booking

## Future Enhancements

1. **Planned Features**:
   - Worker availability calendar
   - Automatic worker matching
   - Dynamic pricing based on demand
   - Worker performance analytics
   - Multi-service bookings
   - Recurring booking packages

2. **API Development**:
   - RESTful API for worker management
   - Real-time availability checking
   - Price calculation endpoints
   - Package management API

3. **Integration Points**:
   - Payment gateway integration
   - SMS/WhatsApp notifications
   - Worker mobile app
   - Customer booking app

## Support

For questions or issues:
- Check Django admin for configuration
- Review model definitions in `workers/models.py`
- Consult pricing examples in this documentation
- Contact development team for complex scenarios