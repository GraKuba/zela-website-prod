"""
Service-specific booking flow configurations.
Defines the sequence of steps for each service type.
"""

# Define the booking flow for each service
BOOKING_FLOWS = {
    'indoor-cleaning': [
        'address',
        'property',
        'duration',
        'schedule', 
        'worker',
        'payment',
        'review'
    ],
    'house-cleaning': [  # Same as indoor-cleaning
        'address',
        'property', 
        'duration',
        'schedule',
        'worker',
        'payment',
        'review'
    ],
    'office-cleaning': [
        'address',
        'property',
        'duration',
        'schedule',
        'worker',
        'payment',
        'review'
    ],
    'outdoor-services': [
        'address',
        'service-config',  # Garden area and service type
        'schedule',
        'worker',
        'payment',
        'review'
    ],
    'moving-cleaning': [
        'address',
        'property',
        'service-config',  # Move type selection
        'schedule',
        'worker',
        'payment',
        'review'
    ],
    'express-cleaning': [
        'address',
        'duration',  # Simple duration slider
        'schedule',
        'worker',
        'payment',
        'review'
    ],
    'laundry-ironing': [
        'address',
        'service-config',  # Items/weight and service options
        'schedule',
        'worker',
        'payment',
        'review'
    ],
    'electrician': [
        'address',
        'property',
        'service-config',  # Electrician specific config
        'schedule',
        'worker',
        'payment',
        'review'
    ],
    'ac-repair': [
        'address',
        'service-config',  # AC units count
        'schedule',
        'worker',
        'payment',
        'review'
    ],
    'pest-control': [
        'address',
        'property',
        'service-config',  # Pest type and treatment
        'schedule',
        'worker',
        'payment',
        'review'
    ],
    'dog-trainer': [
        'address',
        'service-config',  # Package selection
        'schedule',
        'worker',
        'payment',
        'review'
    ],
}

# Default flow for unknown services
DEFAULT_FLOW = [
    'address',
    'schedule',
    'worker',
    'payment',
    'review'
]


def get_service_flow(service_slug: str) -> list:
    """
    Get the flow steps for a specific service.
    
    Args:
        service_slug: The service identifier
        
    Returns:
        List of step names in order
    """
    return BOOKING_FLOWS.get(service_slug, DEFAULT_FLOW)


def get_step_config(service_slug: str, step_name: str) -> dict:
    """
    Get configuration for a specific step in a service flow.
    
    Args:
        service_slug: The service identifier
        step_name: The step name
        
    Returns:
        Configuration dictionary for the step
    """
    # Step-specific configurations
    step_configs = {
        'indoor-cleaning': {
            'duration': {
                'min_hours': 3.5,
                'max_hours': 10,
                'default_hours': 4,
                'show_tasks': True
            },
            'property': {
                'required_fields': ['property_type', 'bedrooms', 'bathrooms'],
                'show_sqm': True
            }
        },
        'express-cleaning': {
            'duration': {
                'min_hours': 2,
                'max_hours': 4,
                'default_hours': 2,
                'show_tasks': False
            }
        },
        'electrician': {
            'service-config': {
                'template': 'electrician_config',
                'fields': ['issue_type', 'urgency', 'description']
            }
        },
        'ac-repair': {
            'service-config': {
                'template': 'ac_units',
                'fields': ['unit_count', 'service_type']
            }
        },
        'pest-control': {
            'service-config': {
                'template': 'pest_control_config',
                'fields': ['pest_type', 'treatment_type', 'affected_areas']
            }
        },
        'dog-trainer': {
            'service-config': {
                'template': 'dog_trainer_packages',
                'fields': ['package_type', 'dog_count', 'training_goals']
            }
        },
    }
    
    service_config = step_configs.get(service_slug, {})
    return service_config.get(step_name, {})


def is_step_required(service_slug: str, step_name: str) -> bool:
    """
    Check if a step is required for a service.
    
    Args:
        service_slug: The service identifier
        step_name: The step name
        
    Returns:
        True if the step is required
    """
    flow = get_service_flow(service_slug)
    return step_name in flow


def get_next_step(service_slug: str, current_step: str) -> str:
    """
    Get the next step in the flow.
    
    Args:
        service_slug: The service identifier
        current_step: The current step name
        
    Returns:
        The next step name or None if at the end
    """
    flow = get_service_flow(service_slug)
    try:
        current_index = flow.index(current_step)
        if current_index < len(flow) - 1:
            return flow[current_index + 1]
    except (ValueError, IndexError):
        pass
    return None


def get_previous_step(service_slug: str, current_step: str) -> str:
    """
    Get the previous step in the flow.
    
    Args:
        service_slug: The service identifier
        current_step: The current step name
        
    Returns:
        The previous step name or None if at the beginning
    """
    flow = get_service_flow(service_slug)
    try:
        current_index = flow.index(current_step)
        if current_index > 0:
            return flow[current_index - 1]
    except (ValueError, IndexError):
        pass
    return None