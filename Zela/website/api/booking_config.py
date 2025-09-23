"""
API endpoints for booking flow configuration
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from services.models import ServiceCategory, ServiceTask
from workers.models import PropertyTypology


@require_http_methods(["GET"])
def get_service_config(request):
    """Get service configuration for booking flow."""
    service_slug = request.GET.get('service', 'indoor-cleaning')
    
    # Map frontend service slugs to database slugs
    # Services from the image: Limpeza Interna, Serviços Externos, Limpeza de Escritório,
    # Limpeza de Mudança, Limpeza Expresso, Lavandaria e Engomadoria
    # Plus trade services: Electrician, AC Repair, Pest Control, Dog Trainer
    service_mapping = {
        # Short URL slugs to database slugs
        'indoor-cleaning': 'indoor-cleaning',          # Limpeza Interna
        'indoor': 'indoor-cleaning',                   # Alternative short form
        'outdoor': 'outdoor-cleaning',                 # Serviços Externos
        'office': 'office-cleaning',                   # Limpeza de Escritório
        'moving': 'moving',                            # Limpeza de Mudança
        'express': 'express-cleaning',                 # Limpeza Expresso
        'laundry': 'laundry-ironing',                  # Lavandaria e Engomadoria
        'electrician': 'electrician',                  # Eletricista
        'ac-repair': 'ac-repair',                      # Reparação de AC
        'pest-control': 'pest-control',                # Desinfestação
        'dog-trainer': 'dog-trainer',                  # Adestrador
    }
    
    db_slug = service_mapping.get(service_slug, service_slug)
    
    # Default configurations for different service types
    # Based on the correct services from the image
    default_configs = {
            # Cleaning Services
            'indoor-cleaning': {  # Limpeza Interna
                'flow_type': 'custom',  # Changed to custom for full control
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                    {'name': 'duration_tasks', 'component': 'screen-8-booking-details'},
                    {'name': 'worker', 'component': 'screen-choose-worker'},
                    {'name': 'payment', 'component': 'screen-13-payment-method'}
                ],
                'pricing_model': 'hourly_minimum',
                'validations': {
                    'require_property_type': True,
                    'min_duration': 3.5,
                    'max_duration': 10
                }
            },
            'office-cleaning': {  # Limpeza de Escritório
                'flow_type': 'custom',  # Changed to custom for full control
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                    {'name': 'duration_tasks', 'component': 'screen-8-booking-details'},
                    {'name': 'worker', 'component': 'screen-choose-worker'},
                    {'name': 'payment', 'component': 'screen-13-payment-method'}
                ],
                'pricing_model': 'hourly_minimum',
                'validations': {
                    'require_property_type': True,
                    'min_duration': 2,
                    'max_duration': 8
                }
            },
            'outdoor-cleaning': {  # Serviços Externos
                'flow_type': 'custom',
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'garden_area', 'component': 'screen-generic-selection'},
                    {'name': 'service_type', 'component': 'screen-generic-selection'},
                    {'name': 'worker', 'component': 'screen-choose-worker'},
                    {'name': 'payment', 'component': 'screen-13-payment-method'}
                ],
                'pricing_model': 'hourly',
                'validations': {
                    'require_area_size': True
                }
            },
            'moving': {  # Limpeza de Mudança
                'flow_type': 'custom',  # Changed to custom for full control
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                    {'name': 'move_type', 'component': 'screen-generic-selection'},
                    {'name': 'worker', 'component': 'screen-choose-worker'},
                    {'name': 'payment', 'component': 'screen-13-payment-method'}
                ],
                'pricing_model': 'fixed',
                'validations': {
                    'require_property_type': True
                }
            },
            'express-cleaning': {  # Limpeza Expresso
                'flow_type': 'custom',  # Changed to custom for full control
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'duration', 'component': 'screen-generic-duration'},
                    {'name': 'worker', 'component': 'screen-choose-worker'},
                    {'name': 'payment', 'component': 'screen-13-payment-method'}
                ],
                'pricing_model': 'hourly',
                'validations': {
                    'min_duration': 2,
                    'max_duration': 4
                }
            },
            'laundry-ironing': {  # Lavandaria e Engomadoria
                'flow_type': 'custom',  # Changed to custom for full control
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'items_weight', 'component': 'screen-generic-units'},
                    {'name': 'service_options', 'component': 'screen-generic-selection'},
                    {'name': 'worker', 'component': 'screen-choose-worker'},
                    {'name': 'payment', 'component': 'screen-13-payment-method'}
                ],
                'pricing_model': 'per_unit',
                'validations': {
                    'require_items_count': True
                }
            },
            
            # Trade Services
            'electrician': {  # Eletricista
                'flow_type': 'custom',  # Changed to custom for full control
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                    {'name': 'service_config', 'component': 'screen-4-electrician-config'},
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
            },
            'ac-repair': {  # Reparação de AC
                'flow_type': 'custom',  # Changed to custom for full control
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'unit_count', 'component': 'screen-3-ac-units'},
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
            },
            'pest-control': {  # Desinfestação
                'flow_type': 'custom',  # Changed to custom for full control
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'property_typology', 'component': 'screen-2-property-typology'},
                    {'name': 'pest_config', 'component': 'screen-5-pest-control-config'},
                    {'name': 'worker', 'component': 'screen-choose-worker'},
                    {'name': 'payment', 'component': 'screen-13-payment-method'}
                ],
                'pricing_model': 'fixed_typology',
                'service_types': {
                    'general': {  # Desinfestação
                        'T1': 10000,
                        'T2': 20000,
                        'T3': 35000,
                        'T4+': 40000
                    },
                    'deratization': {  # Deratização
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
            },
            'dog-trainer': {  # Adestrador
                'flow_type': 'custom',  # Changed to custom for full control
                'required_screens': [
                    {'name': 'address', 'component': 'screen-1-address-capture'},
                    {'name': 'package_selection', 'component': 'screen-6-dog-trainer-packages'},
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
        }
    
    try:
        service_category = ServiceCategory.objects.get(slug=db_slug, is_active=True)
        
        # Build configuration based on service type
        booking_requirements = service_category.booking_requirements or {}
        
        # Use custom booking requirements if available, otherwise use defaults
        if not booking_requirements or not booking_requirements.get('flow_type'):
            booking_requirements = default_configs.get(db_slug, {
                'flow_type': 'standard',
                'required_screens': [],
                'pricing_model': 'fixed'
            })
        
        # Get service tasks
        tasks = []
        for task in service_category.tasks.filter(is_active=True).order_by('order'):
            tasks.append({
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'price': float(task.price),
                'duration_hours': float(task.duration_hours),
                'is_addon': task.is_addon,
                'pricing_model': task.get_pricing_model(),
                'pricing_config': task.pricing_config
            })
        
        # Build response
        config = {
            'id': service_category.id,
            'name': service_category.name,
            'slug': service_category.slug,
            'description': service_category.description,
            'icon': service_category.icon,
            'worker_model_type': service_category.worker_model_type,
            'pricing_model': service_category.pricing_model,
            'booking_requirements': booking_requirements,
            'tasks': tasks,
            'property_typologies': []
        }
        
        # Add property typologies if needed
        if booking_requirements.get('flow_type') == 'property_based':
            typologies = PropertyTypology.objects.all().order_by('name')
            for typology in typologies:
                config['property_typologies'].append({
                    'name': typology.name,
                    'display_name': typology.get_name_display(),
                    'description': typology.description,
                    'typical_sqm': typology.typical_sqm
                })
        
        return JsonResponse(config)
        
    except ServiceCategory.DoesNotExist:
        # Check if we have a default configuration for this service
        if db_slug in default_configs:
            config = default_configs[db_slug]
            service_name_map = {
                'indoor-cleaning': 'Limpeza Interna',
                'office-cleaning': 'Limpeza de Escritório',
                'outdoor-cleaning': 'Serviços Externos',
                'moving': 'Limpeza de Mudança',
                'express-cleaning': 'Limpeza Express',
                'laundry-ironing': 'Lavandaria e Engomadoria',
                'electrician': 'Eletricista',
                'ac-repair': 'Reparação de AC',
                'pest-control': 'Desinfestação',
                'dog-trainer': 'Adestrador'
            }
            
            return JsonResponse({
                'id': 0,
                'name': service_name_map.get(db_slug, 'Service'),
                'slug': db_slug,
                'description': f'{service_name_map.get(db_slug, "Service")} professional service',
                'booking_requirements': config,
                'tasks': [],
                'property_typologies': []
            })
        else:
            # Return generic default configuration
            return JsonResponse({
                'id': 0,
                'name': 'Limpeza Interna',
                'slug': 'indoor-cleaning',
                'description': 'Limpeza completa e profissional da sua casa',
                'booking_requirements': {
                    'flow_type': 'standard',
                    'required_screens': [],
                    'pricing_model': 'fixed'
                },
                'tasks': []
            })