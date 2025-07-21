from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from accounts.models import PaymentMethod


@login_required
@require_http_methods(["GET"])
def get_payment_methods(request):
    """Get user's saved payment methods."""
    user = request.user
    
    # Get all payment methods for the user
    payment_methods = PaymentMethod.objects.filter(
        user=user,
        is_active=True
    ).order_by('-is_default', '-created_at')
    
    # Format the response
    cards = []
    for method in payment_methods:
        cards.append({
            'id': str(method.id),
            'last4': method.last4,
            'brand': method.card_brand,
            'exp_month': method.exp_month,
            'exp_year': method.exp_year,
            'is_default': method.is_default,
        })
    
    # If no cards exist, return mock data for demo
    if not cards:
        cards = [
            {
                'id': 'demo-1',
                'last4': '4242',
                'brand': 'Visa',
                'exp_month': 12,
                'exp_year': 25,
                'is_default': True,
            },
            {
                'id': 'demo-2',
                'last4': '5555',
                'brand': 'Mastercard',
                'exp_month': 6,
                'exp_year': 26,
                'is_default': False,
            }
        ]
    
    return JsonResponse({
        'status': 'success',
        'cards': cards
    })