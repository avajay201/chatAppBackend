from django.db import models
from accounts.models import User
from django.utils.timezone import now


class Addon(models.Model):
    ADDON_TYPE_CHOICES = [
        ('message', 'Message'),
        ('call', 'Call')
    ]

    type = models.CharField(
        max_length=7,
        choices=ADDON_TYPE_CHOICES,
    )

    messages = models.PositiveIntegerField(default=0)
    calls = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_type_display()} Addon"

class Subscription(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    time_period = models.PositiveIntegerField() # months
    messages = models.PositiveIntegerField() # messages
    calls = models.PositiveIntegerField() # minutes
    addons = models.ManyToManyField(Addon, related_name='subscriptions', blank=True)

    def __str__(self):
        return self.name

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)  # Unique coupon code
    discount = models.DecimalField(max_digits=10, decimal_places=2)  # Discount value
    valid_from = models.DateTimeField()  # Start date
    valid_to = models.DateTimeField()  # End date
    is_active = models.BooleanField(default=True)  # Whether the coupon is currently active
    usage_limit = models.PositiveIntegerField(null=True, blank=True)  # Max times the coupon can be used
    usage_count = models.PositiveIntegerField(default=0)  # How many times it has been used

    def __str__(self):
        return self.code

    def is_valid(self):
        """
        Check if the coupon is valid (active, within date range, and usage limit not exceeded).
        """
        now_time = now()
        return (
            self.is_active and
            self.valid_from <= now_time <= self.valid_to and
            (self.usage_limit is None or self.usage_count < self.usage_limit)
        )

class UserSubscription(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    addons = models.ManyToManyField(Addon, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    txn_id = models.CharField(max_length=255, unique=True)
    mihpayid = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mode = models.CharField(max_length=50)
    product_info = models.CharField(max_length=255)
    firstname = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    status = models.CharField(max_length=50)
    coupon = models.CharField(max_length=255, null=True, blank=True)
    card_category = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    messages = models.PositiveIntegerField(default=0) # messages
    calls = models.PositiveIntegerField(default=0) # minutes

    def __str__(self):
        return f"Payment {self.txn_id} - {self.status}"
