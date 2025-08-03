"""
Views module for the booking application.

This module defines the API endpoints for managing users, properties, bookings, payments, reviews, and messages.
It includes custom permission classes for enforcing ownership and access control.
All views are implemented using Django REST Framework viewsets for CRUD operations.
"""

from rest_framework import viewsets, filters, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny, IsAdminUser
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

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
class IsPropertyHost(IsAuthenticated):
    """Only property hosts can modify their properties."""
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.host == request.user


class IsBookingOwner(IsAuthenticated):
    """Only the booking owner can modify or cancel a booking."""
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.user == request.user


class IsReviewOwner(IsAuthenticated):
    """Only the author of a review can edit or delete it."""
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.user == request.user


class IsMessageSender(IsAuthenticated):
    """Only the sender of a message can edit or delete it."""
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.sender == request.user


# -------------------------
# VIEWS
# -------------------------

@extend_schema(
    tags=["Users"],
    summary="Retrieve user information",
    description="Provides read-only access to user profiles. Intended for public profile data retrieval.",
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = NestedUserSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Properties"],
    summary="Manage property listings",
    description="View, create, update, and delete properties. Only property owners can edit or delete their listings.",
    responses={
        200: OpenApiResponse(
            response=NestedPropertySerializer,
            description="List of properties retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Property example",
                    value={
                        "id": 1,
                        "name": "Beach House",
                        "location": "Miami, FL",
                        "price_per_night": 200,
                        "host": 3
                    }
                )
            ],
        )
    }
)
class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = NestedPropertySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    def get_queryset(self):
        return super().get_queryset()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsPropertyHost]
        elif self.action == 'create':
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
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
                        "id": 12,
                        "property": 5,
                        "user": 3,
                        "check_in": "2025-08-01",
                        "check_out": "2025-08-05",
                        "status": "confirmed"
                    }
                )
            ],
        )
    }
)
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Booking.objects.filter(Q(user=user) | Q(property__host=user)).distinct()
        return Booking.objects.none()

    def get_permissions(self):
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
                        "id": 1,
                        "booking": 12,
                        "amount": 400,
                        "status": "completed",
                        "date": "2025-08-01"
                    }
                )
            ],
        )
    }
)
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Payment.objects.filter(Q(booking__user=user) | Q(booking__property__host=user)).distinct()
        return Payment.objects.none()

    def get_permissions(self):
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
                        "id": 3,
                        "property": 1,
                        "user": 5,
                        "rating": 4,
                        "comment": "Great stay, loved the place!",
                        "date": "2025-07-15"
                    }
                )
            ],
        )
    }
)
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsReviewOwner]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in self.permission_classes]


@extend_schema(
    tags=["Messages"],
    summary="Send and receive user messages",
    description="Authenticated users can send messages to each other. A user can only view messages they sent or received. Only senders can edit or delete messages.",
    responses={
        200: OpenApiResponse(
            response=MessageSerializer,
            description="List of messages retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Message example",
                    value={
                        "id": 7,
                        "sender": 3,
                        "receiver": 4,
                        "content": "Hi, is the property available?",
                        "timestamp": "2025-08-01T14:30:00Z"
                    }
                )
            ],
        )
    }
)
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Message.objects.filter(Q(sender=user) | Q(receiver=user)).distinct()
        return Message.objects.none()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsMessageSender]
        else:
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]
