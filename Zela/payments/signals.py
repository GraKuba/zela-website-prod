from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment, Payout, RecentTransaction


@receiver(post_save, sender=Payment)
def create_payment_transaction(sender, instance, created, **kwargs):
    """Create a RecentTransaction when a Payment is created or updated."""
    if created:
        # Create a new transaction for the payment
        RecentTransaction.objects.create(
            user=instance.booking.customer,
            transaction_type='payment',
            reference=instance.reference,
            amount=instance.amount,
            status=instance.status,
            description=f'Payment for {instance.booking.service_task.name if instance.booking.service_task else "Service"}',
            payment=instance,
            metadata={
                'booking_id': instance.booking.id,
                'gateway': instance.gateway,
            }
        )
    else:
        # Update existing transaction if payment status changed
        try:
            transaction = RecentTransaction.objects.get(payment=instance)
            transaction.status = instance.status
            transaction.save()
        except RecentTransaction.DoesNotExist:
            # Create transaction if it doesn't exist
            RecentTransaction.objects.create(
                user=instance.booking.customer,
                transaction_type='payment',
                reference=instance.reference,
                amount=instance.amount,
                status=instance.status,
                description=f'Payment for {instance.booking.service_task.name if instance.booking.service_task else "Service"}',
                payment=instance,
                metadata={
                    'booking_id': instance.booking.id,
                    'gateway': instance.gateway,
                }
            )


@receiver(post_save, sender=Payout)
def create_payout_transaction(sender, instance, created, **kwargs):
    """Create a RecentTransaction when a Payout is created or updated."""
    if created:
        # Create a new transaction for the payout
        RecentTransaction.objects.create(
            user=instance.provider,
            transaction_type='payout',
            amount=instance.net_amount,
            status=instance.status,
            description=f'Weekly payout for {instance.week_display}',
            payout=instance,
            metadata={
                'week_start': str(instance.week_start),
                'week_end': str(instance.week_end),
                'gross_amount': instance.amount,
                'commission_amount': instance.commission_amount,
                'commission_rate': float(instance.commission_rate),
            }
        )
        
        # Also create a commission transaction
        if instance.commission_amount > 0:
            RecentTransaction.objects.create(
                user=instance.provider,
                transaction_type='commission',
                amount=instance.commission_amount,
                status=instance.status,
                description=f'Platform commission for {instance.week_display}',
                payout=instance,
                metadata={
                    'week_start': str(instance.week_start),
                    'week_end': str(instance.week_end),
                    'commission_rate': float(instance.commission_rate),
                }
            )
    else:
        # Update existing transactions if payout status changed
        RecentTransaction.objects.filter(payout=instance).update(status=instance.status)