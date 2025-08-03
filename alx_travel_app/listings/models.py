# alx_travel_app/listings/models.py

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser # For custom User model
from django.core.validators import MinValueValidator, MaxValueValidator

# --- User Model ---
# Extending Django's AbstractUser to match the provided specification.
class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Includes user_id as PK, explicit email uniqueness, phone_number, and role.
    """
    # user_id: Primary Key, UUID, Indexed (overrides default 'id')
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # first_name: VARCHAR, NOT NULL (overrides AbstractUser's blank=True)
    first_name = models.CharField(max_length=150, null=False, blank=False)

    # last_name: VARCHAR, NOT NULL (overrides AbstractUser's blank=True)
    last_name = models.CharField(max_length=150, null=False, blank=False)

    # email: VARCHAR, UNIQUE, NOT NULL (overrides AbstractUser's non-unique email)
    email = models.EmailField(unique=True, null=False, blank=False, verbose_name='email address')

    # password_hash: VARCHAR, NOT NULL (handled by AbstractUser's 'password' field internally)
    # No need to explicitly define 'password_hash'; Django handles it with the 'password' field.

    # phone_number: VARCHAR, NULL
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    # role: ENUM (guest, host, admin), NOT NULL
    class RoleChoices(models.TextChoices):
        GUEST = 'guest', 'Guest'
        HOST = 'host', 'Host'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=10, choices=RoleChoices.choices, default=RoleChoices.GUEST, null=False)

    # created_at: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP (Explicitly defined)
    created_at = models.DateTimeField(auto_now_add=True)

    # Configure AbstractUser to use 'email' for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Fields required for createsuperuser

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-created_at'] # Order by our custom created_at
        indexes = [
            models.Index(fields=['email']), # Additional index on email as per spec
        ]

    def __str__(self):
        return self.email

# Get the User model for ForeignKey references after its definition
from django.contrib.auth import get_user_model
CustomUser = get_user_model()


# --- Property Model ---
class Property(models.Model):
    """
    Represents a property listing available for booking.
    Corresponds to 'Listing' in previous iteration, renamed to 'Property' as per spec.
    """
    property_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)
    host = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='properties') # host_id in spec
    name = models.CharField(max_length=255, null=False) # Changed from 'title' to 'name'
    description = models.TextField(null=False)
    location = models.CharField(max_length=255, null=False) # Changed from address/city/country composite
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property_id']), # Primary key is automatically indexed, but explicit for clarity
        ]

    def __str__(self):
        return self.name

# --- Booking Model ---
class Booking(models.Model):
    """
    Represents a booking made by a guest for a specific property.
    """
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings') # property_id in spec
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings') # user_id in spec
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    # status: ENUM (pending, confirmed, canceled), NOT NULL
    class BookingStatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELED = 'canceled', 'Canceled'

    status = models.CharField(
        max_length=10,
        choices=BookingStatusChoices.choices,
        default=BookingStatusChoices.PENDING,
        null=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property']),   # Additional index on property_id
            models.Index(fields=['booking_id']), # Primary key is automatically indexed, but explicit for clarity
        ]
        # Consider adding a unique_together constraint or custom validation
        # to prevent overlapping bookings for the same property.

    def __str__(self):
        return f"Booking {self.booking_id} for {self.property.name} by {self.user.username}"


# --- Payment Model ---
class Payment(models.Model):
    """
    Records payment details for a booking.
    """
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments') # booking_id in spec
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    payment_date = models.DateTimeField(auto_now_add=True) # Matches 'TIMESTAMP, DEFAULT CURRENT_TIMESTAMP'

    # payment_method: ENUM (credit_card, paypal, stripe), NOT NULL
    class PaymentMethodChoices(models.TextChoices):
        CREDIT_CARD = 'credit_card', 'Credit Card'
        PAYPAL = 'paypal', 'PayPal'
        STRIPE = 'stripe', 'Stripe'

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethodChoices.choices,
        null=False,
    )

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['booking']),    # Additional index on booking_id
            models.Index(fields=['payment_id']), # Primary key is automatically indexed, but explicit for clarity
        ]

    def __str__(self):
        return f"Payment {self.payment_id} for Booking {self.booking.booking_id} - {self.amount}"


# --- Review Model ---
class Review(models.Model):
    """
    Represents a review left by a user for a property.
    """
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews') # property_id in spec
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews') # user_id in spec
    rating = models.IntegerField(
        null=False,
        validators=[MinValueValidator(1), MaxValueValidator(5)], # CHECK: rating >= 1 AND rating <= 5
        help_text='Rating must be between 1 and 5.'
    )
    comment = models.TextField(null=False) # TEXT, NOT NULL (changed from previous assumption)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property']), # Additional index on property_id
        ]
        # Optional: Ensure a user can only leave one review per property
        unique_together = ('property', 'user')

    def __str__(self):
        return f"Review {self.rating}/5 for {self.property.name} by {self.user.username}"


# --- Message Model ---
class Message(models.Model):
    """
    Represents a direct message between two users.
    """
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages') # sender_id in spec
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages') # recipient_id in spec
    message_body = models.TextField(null=False)
    sent_at = models.DateTimeField(auto_now_add=True) # Matches 'TIMESTAMP, DEFAULT CURRENT_TIMESTAMP'

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['sender', 'sent_at']),
            models.Index(fields=['recipient', 'sent_at']),
        ]

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}: {self.message_body[:50]}..."