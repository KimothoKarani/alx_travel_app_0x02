"""
Views module for the booking application.

This module defines the API endpoints for managing users, properties, bookings, payments, reviews, and messages.
It includes custom permission classes for enforcing ownership and access control.
All views are implemented using Django REST Framework viewsets for CRUD operations.

--- DRF-SPECTACULAR DOCUMENTATION GENERATION ---

drf-spectacular automatically introspects DRF ViewSets, serializers, and URL patterns
to generate an OpenAPI schema (your API blueprint). The `extend_schema` decorator
is used to provide additional metadata, examples, and overrides that cannot be
automatically inferred or to make the documentation more explicit and user-friendly.

For each ViewSet, drf-spectacular will typically generate:
- A `/tag` (e.g., /users, /properties) for the list endpoint (GET, POST).
- A `/tag/{pk}` (e.g., /users/{user_id}, /properties/{property_id}) for the detail endpoint (GET, PUT, PATCH, DELETE).
- The HTTP methods available for each endpoint based on the ViewSet type (e.g., ReadOnlyModelViewSet only supports GET).
- Request/response schemas based on the assigned `serializer_class`.
- Security requirements based on `permission_classes` and `authentication_classes` defined in REST_FRAMEWORK settings.
- Custom descriptions, summaries, and examples specified via `@extend_schema`.
"""

from rest_framework import viewsets, filters, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny, IsAdminUser
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, inline_serializer # Import inline_serializer for complex examples
from rest_framework import serializers # Needed for inline_serializer

from .serializers import (
    NestedUserSerializer,
    PropertySerializer,
    NestedPropertySerializer,
    BookingSerializer,
    MessageSerializer,
    ReviewSerializer,
    PaymentSerializer
)
from .models import User, Property, Booking, Payment, Review, Message


# -------------------------
# CUSTOM PERMISSIONS
# -------------------------
# drf-spectacular will infer that these permission classes are applied
# and will typically show `Bearer Auth` (from your JWT settings) as a security requirement
# for methods where IsAuthenticated or its subclasses are used.

class IsPropertyHost(IsAuthenticated):
    """Only property hosts can modify their properties."""
    def has_object_permission(self, request, view, obj):
        # Allow read-only access for anyone (handled by ViewSet permissions usually)
        # or allow modification/deletion only if the user is the host of the property.
        return request.method in permissions.SAFE_METHODS or obj.host == request.user


class IsBookingOwner(IsAuthenticated):
    """Only the booking owner can modify or cancel a booking."""
    def has_object_permission(self, request, view, obj):
        # Allow read-only access or allow modification/deletion only if the user is the booking's owner.
        return request.method in permissions.SAFE_METHODS or obj.user == request.user


class IsReviewOwner(IsAuthenticated):
    """Only the author of a review can edit or delete it."""
    def has_object_permission(self, request, view, obj):
        # Allow read-only access or allow modification/deletion only if the user is the review's author.
        return request.method in permissions.SAFE_METHODS or obj.user == request.user


class IsMessageSender(IsAuthenticated):
    """Only the sender of a message can edit or delete it."""
    def has_object_permission(self, request, view, obj):
        # Allow read-only access or allow modification/deletion only if the user is the message's sender.
        return request.method in permissions.SAFE_METHODS or obj.sender == request.user


# -------------------------
# VIEWS
# -------------------------

@extend_schema(
    tags=["Users"], # Organizes this ViewSet under the "Users" tag in Swagger UI
    summary="Retrieve user information", # Short summary for the endpoint group
    description="Provides read-only access to user profiles. Intended for public profile data retrieval.", # Detailed description
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed.
    As a ReadOnlyModelViewSet, it will generate:
    - GET /users/ (list all users)
    - GET /users/{user_id}/ (retrieve a specific user)

    The schema for request/response will be based on NestedUserSerializer.
    """
    queryset = User.objects.all()
    serializer_class = NestedUserSerializer
    permission_classes = [AllowAny] # drf-spectacular will infer no authentication/authorization is needed for these endpoints


@extend_schema(
    tags=["Properties"],
    summary="Manage property listings",
    description="View, create, update, and delete properties. Only property owners can edit or delete their listings.",
    # Responses can be defined globally for the ViewSet or per-method if needed.
    responses={
        # Using `OpenApiResponse` with a serializer for automatic schema generation
        200: OpenApiResponse(
            response=NestedPropertySerializer,
            description="List of properties retrieved successfully.",
            examples=[
                # Examples provide concrete data to illustrate response structure
                OpenApiExample(
                    "Property example", # Name of the example
                    value={ # The example data (should match serializer schema)
                        "property_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "name": "Cozy Beachfront Villa",
                        "description": "Stunning views, private beach access.",
                        "location": "Malibu, CA",
                        "price_per_night": "500.00",
                        "created_at": "2024-01-01T10:00:00Z",
                        "updated_at": "2024-01-01T10:00:00Z",
                        "host": { # Assuming NestedUserSerializer for host in NestedPropertySerializer
                            "user_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef0",
                            "first_name": "Jane",
                            "last_name": "Doe",
                            "email": "jane.doe@example.com",
                            "phone_number": "555-123-4567",
                            "role": "host"
                        }
                    },
                    media_type="application/json", # Specify media type if not default
                )
            ],
        ),
        # You can add more specific responses for other status codes (e.g., 401, 403, 404)
        401: OpenApiResponse(description="Authentication credentials were not provided."),
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="Property not found."),
    }
)
class PropertyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows properties to be viewed, created, updated, or deleted.
    As a ModelViewSet, it will generate:
    - GET /properties/ (list all properties)
    - POST /properties/ (create a new property)
    - GET /properties/{property_id}/ (retrieve a specific property)
    - PUT /properties/{property_id}/ (full update of a property)
    - PATCH /properties/{property_id}/ (partial update of a property)
    - DELETE /properties/{property_id}/ (delete a property)

    The schema for request/response will be based on NestedPropertySerializer.
    Permissions are dynamically set in `get_permissions`.
    """
    queryset = Property.objects.all()
    serializer_class = NestedPropertySerializer
    permission_classes = [IsAuthenticatedOrReadOnly] # Default for non-create/update/delete actions

    def perform_create(self, serializer):
        """
        Overrides the default create method to automatically assign the current
        authenticated user as the 'host' of the new property.
        drf-spectacular will infer that 'host' field is read-only in the request body
        for POST operations due to this `perform_create` method.
        """
        serializer.save(host=self.request.user)

    def get_queryset(self):
        """
        This method is not strictly necessary here unless you have specific filtering
        logic for retrieving properties (e.g., only show user's own properties).
        Currently, it returns all properties from the base queryset.
        drf-spectacular generally infers the queryset for schema generation,
        but complex filtering here won't be explicitly documented without
        manual `@extend_schema` modifications.
        """
        return super().get_queryset()

    def get_permissions(self):
        """
        Dynamically sets permission classes based on the action being performed.
        drf-spectacular will interpret these permissions for each generated endpoint/method.
        - 'create' requires IsAuthenticated.
        - 'update', 'partial_update', 'destroy' require IsAuthenticated AND IsPropertyHost.
        - Other actions (like 'list', 'retrieve') use the default IsAuthenticatedOrReadOnly.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsPropertyHost]
        elif self.action == 'create':
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny] # Changed to AllowAny as per IsAuthenticatedOrReadOnly logic
        return [permission() for permission in self.permission_classes]


@extend_schema(
    tags=["Bookings"],
    summary="Manage bookings",
    description="Authenticated users can create and view their bookings. Hosts can view bookings for their properties. Only booking creators can modify or cancel bookings.",
    responses={
        200: OpenApiResponse(
            response=BookingSerializer,
            description="List of bookings retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Booking example",
                    value={
                        "booking_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "property": "some-property-id", # Assuming PropertySerializer's representation of property
                        "user": "some-user-id",         # Assuming UserSerializer's representation of user
                        "start_date": "2025-08-01",
                        "end_date": "2025-08-05",
                        "total_price": "800.00",
                        "status": "confirmed",
                        "created_at": "2025-07-20T10:00:00Z"
                    },
                    media_type="application/json",
                )
            ],
        )
    }
)
class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows bookings to be viewed, created, updated, or deleted.
    This ViewSet will generate standard CRUD endpoints for bookings.
    The `get_queryset` method dynamically filters bookings based on the requesting user's role
    (owner of booking OR host of property). drf-spectacular cannot auto-document this complex
    filtering; the description above helps.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated] # Default for all actions unless overridden below

    def perform_create(self, serializer):
        """
        Assigns the current authenticated user as the 'user' (booker) for the new booking.
        The 'user' field will be implicitly read-only for creation in the schema.
        """
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """
        Custom queryset to ensure users can only see their own bookings OR
        bookings made for properties they host.
        `Q(user=user)`: bookings where the requesting user is the booker.
        `Q(property__host=user)`: bookings for properties where the requesting user is the host.
        `distinct()`: handles cases where a user might be both (though unlikely for a single booking).
        """
        user = self.request.user
        if user.is_authenticated:
            return Booking.objects.filter(Q(user=user) | Q(property__host=user)).distinct()
        return Booking.objects.none() # Return empty queryset if user is not authenticated

    def get_permissions(self):
        """
        Dynamically sets permission classes for Booking actions.
        - 'update', 'partial_update', 'destroy' require IsAuthenticated AND IsBookingOwner.
        - Other actions (list, retrieve, create) require IsAuthenticated.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsBookingOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]


@extend_schema(
    tags=["Payments"],
    summary="Handle payments for bookings",
    description="View and create payments related to bookings. Only admins can update or delete payments.",
    responses={
        200: OpenApiResponse(
            response=PaymentSerializer,
            description="List of payments retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Payment example",
                    value={
                        "payment_id": "e6f7g8h9-i0j1-2345-6789-0abcdef12345",
                        "booking": "some-booking-id", # Assuming BookingSerializer's representation of booking
                        "amount": "400.00",
                        "payment_date": "2025-08-01T10:00:00Z",
                        "payment_method": "credit_card"
                    },
                    media_type="application/json",
                )
            ],
        )
    }
)
class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows payments to be viewed, created, updated, or deleted.
    This ViewSet generates standard CRUD endpoints for payments.
    The `get_queryset` limits access to payments related to the user's bookings
    or properties they host.
    Update/delete actions are restricted to admin users.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated] # Default for all actions unless overridden below

    def get_queryset(self):
        """
        Custom queryset to ensure users can only see payments for their bookings
        or payments for properties they host.
        `Q(booking__user=user)`: payments for bookings made by the requesting user.
        `Q(booking__property__host=user)`: payments for bookings on properties where the requesting user is the host.
        """
        user = self.request.user
        if user.is_authenticated:
            return Payment.objects.filter(Q(booking__user=user) | Q(booking__property__host=user)).distinct()
        return Payment.objects.none()

    def get_permissions(self):
        """
        Dynamically sets permission classes for Payment actions.
        - 'create' requires IsAuthenticated.
        - 'update', 'partial_update', 'destroy' require IsAuthenticated AND IsAdminUser.
        - Other actions (list, retrieve) require IsAuthenticated.
        """
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]


@extend_schema(
    tags=["Reviews"],
    summary="Manage property and booking reviews",
    description="Anyone can view reviews. Authenticated users can create reviews. Only review authors can edit or delete them.",
    responses={
        200: OpenApiResponse(
            response=ReviewSerializer,
            description="List of reviews retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Review example",
                    value={
                        "review_id": "f7g8h9i0-j1k2-3456-7890-1abcdef23456",
                        "property": "some-property-id", # Assuming PropertySerializer's representation of property
                        "user": "some-user-id",         # Assuming UserSerializer's representation of user
                        "rating": 5,
                        "comment": "Absolutely loved this place! Clean, spacious, and amazing host.",
                        "created_at": "2025-07-15T12:00:00Z"
                    },
                    media_type="application/json",
                )
            ],
        )
    }
)
class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reviews to be viewed, created, updated, or deleted.
    This ViewSet generates standard CRUD endpoints for reviews.
    Unauthenticated users can view reviews, while creation/modification is restricted.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] # Default for all actions

    def perform_create(self, serializer):
        """
        Assigns the current authenticated user as the author of the new review.
        The 'user' field will be implicitly read-only for creation in the schema.
        """
        serializer.save(user=self.request.user)

    def get_permissions(self):
        """
        Dynamically sets permission classes for Review actions.
        - 'update', 'partial_update', 'destroy' require IsAuthenticated AND IsReviewOwner.
        - Other actions (list, retrieve, create) allow IsAuthenticatedOrReadOnly.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsReviewOwner]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in self.permission_classes]


@extend_schema(
    tags=["Messages"],
    summary="Send and receive user messages",
    description="Authenticated users can send messages to each other. A user can only view messages they sent or received. Only senders can edit or delete messages. Supports threaded conversations.",
    responses={
        200: OpenApiResponse(
            response=MessageSerializer,
            description="List of messages retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Top-level message example",
                    value={
                        "message_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "sender": "sender-user-id",
                        "recipient": "recipient-user-id",
                        "message_body": "Hi, is the property available for these dates?",
                        "sent_at": "2025-08-01T14:30:00Z",
                        "parent_message": None,
                        "replies": []
                    },
                    media_type="application/json",
                ),
                OpenApiExample(
                    "Reply message example",
                    value={
                        "message_id": "f1e2d3c4-b5a6-9876-5432-10fedcba9876",
                        "sender": "recipient-user-id", # Reply from original recipient
                        "recipient": None, # Recipient might be null for a pure reply in a thread
                        "message_body": "Yes, it is! What dates were you thinking?",
                        "sent_at": "2025-08-01T14:35:00Z",
                        "parent_message": "a1b2c3d4-e5f6-7890-1234-567890abcdef", # ID of the parent message
                        "replies": []
                    },
                    media_type="application/json",
                )
            ],
        )
    }
)
class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows messages to be viewed, created, updated, or deleted.
    This ViewSet generates standard CRUD endpoints for messages.
    It supports retrieving messages where the user is either the sender or the recipient.
    The `parent_message` field (in models) and `replies` field (in serializer)
    enable threaded conversations.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated] # Default for all actions

    def perform_create(self, serializer):
        """
        Assigns the current authenticated user as the sender of the new message.
        The 'sender' field will be implicitly read-only for creation in the schema.
        """
        serializer.save(sender=self.request.user)

    def get_queryset(self):
        """
        Custom queryset to ensure users can only see messages they have sent or received.
        If the Message model has `parent_message` for threading, you might further
        refine this to fetch only top-level messages or entire threads efficiently,
        potentially using `prefetch_related` as discussed in previous contexts.
        For now, it gets all messages where user is sender or recipient.
        """
        user = self.request.user
        if user.is_authenticated:
            # Note: If implementing threading strictly, you might want a separate view for top-level
            # messages and then a detail view for a thread, or complex prefetching.
            return Message.objects.filter(Q(sender=user) | Q(recipient=user)).distinct()
        return Message.objects.none()

    def get_permissions(self):
        """
        Dynamically sets permission classes for Message actions.
        - 'update', 'partial_update', 'destroy' require IsAuthenticated AND IsMessageSender.
        - Other actions (list, retrieve, create) require IsAuthenticated.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsMessageSender]
        else:
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]