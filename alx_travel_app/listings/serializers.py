# alx_travel_app/listings/serializers.py

from rest_framework import serializers
from .models import CustomUser, Property, Booking, Review # Import CustomUser and other models

# --- Helper Serializers for Nested Relationships ---

# For nesting User details (host, guest, sender, recipient)
class NestedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser # Use CustomUser here
        fields = ['user_id', 'first_name', 'last_name', 'email'] # Ensure user_id is included
        read_only_fields = fields # Make nested fields read-only

# For nesting Property details (e.g., within a Booking)
class NestedPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['property_id', 'name', 'location', 'pricepernight']
        read_only_fields = fields

# --- Main Serializers for Listing and Booking ---

# Property Serializer (corresponds to Listing model)
class PropertySerializer(serializers.ModelSerializer):
    """
    Serializer for the Property model.
    Handles nested host output and host_id input.
    """
    host = NestedUserSerializer(read_only=True) # Nested output for the host

    # For input, allow specifying host by their user_id
    host_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), # Queryset for validation
        source='host',                     # Maps to the 'host' ForeignKey field
        write_only=True,                   # Only used for writing (input), not shown in output
        help_text='The user_id (UUID) of the host for this property.'
    )

    class Meta:
        model = Property
        fields = [
            'property_id', 'host', 'host_id', 'name', 'description', 'location',
            'pricepernight', 'created_at', 'updated_at'
        ]
        read_only_fields = ['property_id', 'created_at', 'updated_at']

# Booking Serializer
class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model.
    Handles nested property and user output, and their respective ID inputs.
    """
    property = NestedPropertySerializer(read_only=True) # Nested output for the property
    user = NestedUserSerializer(read_only=True)       # Nested output for the user (guest)

    # For input, allow specifying property by its property_id
    property_id = serializers.PrimaryKeyRelatedField(
        queryset=Property.objects.all(),
        source='property',
        write_only=True,
        help_text='The property_id (UUID) of the property being booked.'
    )

    # For input, allow specifying user (guest) by their user_id
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='user',
        write_only=True,
        help_text='The user_id (UUID) of the user making the booking.'
    )

    class Meta:
        model = Booking
        fields = [
            'booking_id', 'property', 'property_id', 'user', 'user_id',
            'start_date', 'end_date', 'total_price', 'status', 'created_at'
        ]
        # booking_id, total_price, status (initial), created_at are typically read-only on creation
        read_only_fields = ['booking_id', 'total_price', 'status', 'created_at']

    # Custom create method to calculate total_price and add initial status.
    def create(self, validated_data):
        property_instance = validated_data.get('property')
        start_date = validated_data.get('start_date')
        end_date = validated_data.get('end_date')

        # Basic validation for dates
        if start_date >= end_date:
            raise serializers.ValidationError("End date must be after start date.")

        num_nights = (end_date - start_date).days
        if num_nights <= 0:
            raise serializers.ValidationError("Booking must be for at least one night.")

        # Calculate total_price
        validated_data['total_price'] = property_instance.pricepernight * num_nights

        # Set default status, though it's already defined in the model
        if 'status' not in validated_data:
            validated_data['status'] = Booking.BookingStatusChoices.PENDING

        return super().create(validated_data)

    # Custom update method to prevent changing immutable fields
    def update(self, instance, validated_data):
        # Prevent changing property or user after creation
        if 'property' in validated_data or 'user' in validated_data:
            raise serializers.ValidationError("Property and user cannot be changed after booking creation.")

        # Allow updating status
        if 'status' in validated_data:
            instance.status = validated_data.pop('status')

        return super().update(instance, validated_data)