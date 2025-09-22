"""
Management command to update/create all service categories for Zela
"""
from django.core.management.base import BaseCommand
from services.models import ServiceCategory, ServiceTask


class Command(BaseCommand):
    help = 'Update or create all service categories with proper configuration'

    def handle(self, *args, **options):
        self.stdout.write('Updating service categories...\n')
        
        # Define all services with their configurations
        services = [
            {
                'name': 'Limpeza Interna',
                'slug': 'indoor-cleaning',
                'icon': '🏠',
                'description': 'Limpeza completa e profissional da sua casa',
                'pricing_model': 'hourly_minimum',
                'worker_model_type': 'generalist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                        {'name': 'duration_tasks', 'component': 'screen-8-booking-details'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'hourly_minimum',
                    'validations': {
                        'require_property_type': True,
                        'min_duration': 3.5,
                        'max_duration': 10
                    }
                }
            },
            {
                'name': 'Serviços Externos',
                'slug': 'outdoor-services',
                'icon': '🌳',
                'description': 'Manutenção de jardins, limpeza de piscinas e serviços externos',
                'pricing_model': 'hourly',
                'worker_model_type': 'specialist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'garden_area', 'component': 'screen-generic-selection'},
                        {'name': 'service_type', 'component': 'screen-generic-selection'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'hourly',
                    'validations': {
                        'require_area_size': True
                    }
                }
            },
            {
                'name': 'Limpeza de Escritório',
                'slug': 'office-cleaning',
                'icon': '🏢',
                'description': 'Limpeza profissional de escritórios e espaços comerciais',
                'pricing_model': 'hourly_minimum',
                'worker_model_type': 'generalist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                        {'name': 'duration_tasks', 'component': 'screen-8-booking-details'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'hourly_minimum',
                    'validations': {
                        'require_property_type': True,
                        'min_duration': 2,
                        'max_duration': 8
                    }
                }
            },
            {
                'name': 'Limpeza de Mudança',
                'slug': 'moving-cleaning',
                'icon': '📦',
                'description': 'Limpeza profunda para mudanças de entrada e saída',
                'pricing_model': 'fixed',
                'worker_model_type': 'generalist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                        {'name': 'move_type', 'component': 'screen-generic-selection'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'fixed',
                    'validations': {
                        'require_property_type': True
                    }
                }
            },
            {
                'name': 'Limpeza Express',
                'slug': 'express-cleaning',
                'icon': '⚡',
                'description': 'Serviço de limpeza rápido para necessidades urgentes',
                'pricing_model': 'hourly',
                'worker_model_type': 'generalist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'duration', 'component': 'screen-generic-duration'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'hourly',
                    'validations': {
                        'min_duration': 2,
                        'max_duration': 4
                    }
                }
            },
            {
                'name': 'Lavandaria e Engomadoria',
                'slug': 'laundry-ironing',
                'icon': '👔',
                'description': 'Serviços profissionais de lavandaria e engomadoria',
                'pricing_model': 'per_unit',
                'worker_model_type': 'specialist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'items_weight', 'component': 'screen-generic-units'},
                        {'name': 'service_options', 'component': 'screen-generic-selection'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'per_unit',
                    'validations': {
                        'require_items_count': True
                    }
                }
            },
            {
                'name': 'Eletricista',
                'slug': 'electrician',
                'icon': '⚡',
                'description': 'Serviços profissionais de eletricidade residencial e comercial',
                'pricing_model': 'hourly_minimum_typology',
                'worker_model_type': 'specialist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                        {'name': 'service_config', 'component': 'screen-4-electrician-config'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'hourly_minimum_typology',
                    'minimum_hours': 2,
                    'hourly_rates': {
                        'T1': 8000,
                        'T2': 9000,
                        'T3': 10000,
                        'T4+': 12000
                    },
                    'validations': {
                        'require_property_type': True,
                        'min_hours': 2
                    }
                }
            },
            {
                'name': 'Reparação de AC',
                'slug': 'ac-repair',
                'icon': '❄️',
                'description': 'Instalação, manutenção e reparação de ar condicionado',
                'pricing_model': 'per_unit_discount',
                'worker_model_type': 'specialist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'unit_count', 'component': 'screen-3-ac-units'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'per_unit_discount',
                    'base_price': 16000,
                    'volume_discounts': {
                        '1': 0,
                        '2-3': 10,
                        '4-5': 15,
                        '6+': 20
                    },
                    'validations': {
                        'require_unit_count': True
                    }
                }
            },
            {
                'name': 'Desinfestação',
                'slug': 'pest-control',
                'icon': '🚫',
                'description': 'Controlo profissional de pragas e desinfestação',
                'pricing_model': 'fixed_typology',
                'worker_model_type': 'specialist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                        {'name': 'pest_config', 'component': 'screen-5-pest-control-config'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'fixed_typology',
                    'service_types': {
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
                    },
                    'validations': {
                        'require_property_type': True,
                        'require_pest_type': True
                    }
                }
            },
            {
                'name': 'Adestrador',
                'slug': 'dog-trainer',
                'icon': '🐕',
                'description': 'Treino profissional e adestramento de cães',
                'pricing_model': 'package',
                'worker_model_type': 'specialist',
                'booking_requirements': {
                    'flow_type': 'custom',
                    'required_screens': [
                        {'name': 'address', 'component': 'screen-1-address-capture'},
                        {'name': 'package_selection', 'component': 'screen-6-dog-trainer-packages'},
                        {'name': 'schedule', 'component': 'screen-7-date-bucket'},
                        {'name': 'worker', 'component': 'screen-choose-worker'},
                        {'name': 'payment', 'component': 'screen-13-payment-method'}
                    ],
                    'pricing_model': 'package',
                    'packages': [
                        {'id': 'evaluation', 'name': 'Sessão de Avaliação', 'sessions': 1, 'price': 15000},
                        {'id': 'single', 'name': 'Sessão Avulsa', 'sessions': 1, 'price': 20000},
                        {'id': 'pack5', 'name': 'Pacote 5 Sessões', 'sessions': 5, 'price': 90000},
                        {'id': 'pack10', 'name': 'Pacote 10 Sessões', 'sessions': 10, 'price': 160000}
                    ],
                    'validations': {
                        'require_package_selection': True
                    }
                }
            },
        ]
        
        # Create or update each service
        for idx, service_data in enumerate(services):
            try:
                # Check if exists, update or create
                service, created = ServiceCategory.objects.update_or_create(
                    slug=service_data['slug'],
                    defaults={
                        'name': service_data['name'],
                        'icon': service_data['icon'],
                        'description': service_data['description'],
                        'pricing_model': service_data['pricing_model'],
                        'worker_model_type': service_data['worker_model_type'],
                        'booking_requirements': service_data['booking_requirements'],
                        'is_active': True,
                        'order': idx
                    }
                )
                
                action = 'Created' if created else 'Updated'
                self.stdout.write(
                    self.style.SUCCESS(f'{action} service: {service.name} ({service.slug})')
                )
                
                # Create basic task for the service if none exist
                if service.tasks.count() == 0:
                    ServiceTask.objects.create(
                        service_category=service,
                        name=f'{service.name} - Serviço Base',
                        description=f'Serviço base de {service.name.lower()}',
                        price=15000.00,  # Base price in AOA
                        duration_hours=2.0,
                        is_addon=False,
                        is_active=True,
                        order=0
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'  - Created base task for {service.name}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating/updating {service_data["name"]}: {str(e)}')
                )
        
        # Deactivate old services not in the list
        old_slugs = ['elder-care', 'house-cleaning']  # Services to deactivate
        ServiceCategory.objects.filter(slug__in=old_slugs).update(is_active=False)
        self.stdout.write(
            self.style.WARNING('Deactivated old services: elder-care, house-cleaning')
        )
        
        self.stdout.write(
            self.style.SUCCESS('\nAll services updated successfully!')
        )
        
        # Display summary
        active_count = ServiceCategory.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal active services: {active_count}')
        )