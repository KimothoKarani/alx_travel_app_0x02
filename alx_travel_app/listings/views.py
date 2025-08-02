from rest_framework import viewsets, filters, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny, IsAdminUser
from django.db.models import Q #For filtering based on user in get_queryset
from .serializers import (NestedUserSerializer, PropertySerializer, NestedPropertySerializer,
                          BookingSerializer, MessageSerializer, ReviewSerializer, PaymentSerializer)

from .models import User, Property, Booking, Payment, Review, Message

# You would define your custom permissions here, e.g., IsOwnerOrReadOnly, IsGuestOwner
# For this task, we'll use DRF's built-in permissions primarily.

class UserViewSet(viewsets.ReadOnlyModelViewSet): # ReadOnly for security, users typically manage their own profile
    queryset = User.objects.all()
    serializer_class = NestedUserSerializer
    permission_classes = [AllowAny]
    # Allow anyone to list users (or IsAuthenticated if sensitive)
    # You might add /me/ endpoint for current user to view/update their own profile
    # permission_classes = [IsAdminUser] # If only admins can list all users


# Placeholder for IsPropertyHost permission (you'd define it in permissions.py)
class IsPropertyHost(IsAuthenticated):
    """
    Custom permission to only allow hosts of a property to edit/delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the property.
        return obj.host == request.user

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = NestedPropertySerializer
    # Allow read-only for anyone, but only authenticated users (who own the property) can modify
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Set the owner of the property to the authenticated user creating it
        serializer.save(host=self.request.user)

    def get_queryset(self):
        # Custom logic for filtering (e.g., only show active properties)
        # Or if you implement ownership permission, the permission class would handle it.
        # For full CRUD, default queryset is fine if permissions control access.
        return super().get_queryset()

    def get_permissions(self):
        """
         Instantiates and returns the list of permissions that this view requires.
         Custom permission for ownership: Only the host can update/delete their own property.
         """
        if self.action in ['update', 'partial_update', 'destroy']:
            # This would typically be a custom permission like IsOwner
            self.permission_classes = [IsAuthenticated, IsPropertyHost]

        elif self.action == 'create':
            self.permission_classes = [IsAuthenticated]
        else: #'list', 'retrieve'
            self.permission_classes = [AllowAny] # Anyone can view

        return [permission() for permission in self.permission_classes]


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    # Only authenticated users can interact with bookings.
    # Needs custom permission for ownership/host view.
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Set the user (guest) making the booking to the authenticated user
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # A user should only see their own bookings (as guest or host of the listing)
        user = self.request.user
        if user.is_authenticated:
            # Filter bookings where user is the guest OR user is the host of the booked property
            return Booking.objects.filter(Q(user=user) | Q(property__host=user)).distinct()
        return Booking.objects.none()  # No bookings for unauthenticated users

    def get_permissions(self):
        # Only the guest who created the booking can update/delete it.
        # Hosts can view, but not necessarily modify another user's booking directly.
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsBookingOwner]  # IsBookingOwner needs to be defined
        else:  # 'list', 'retrieve', 'create'
            self.permission_classes = [IsAuthenticated]  # All authenticated can view/create

        return [permission() for permission in self.permission_classes]


# Placeholder for IsBookingOwner permission (you'd define it in permissions.py)
class IsBookingOwner(IsAuthenticated):
    """
    Custom permission to only allow the user who made the booking to edit/delete it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True  # Any authenticated user can view (handled by get_queryset anyway)

        # Object-level write permissions
        return obj.user == request.user


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    # Permissions: Only authenticated users can manage payments.
    # Needs custom permission: Only user tied to booking or host can view/create.
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Payments related to user's bookings (as guest) or user's properties (as host)
            return Payment.objects.filter(Q(booking__user=user) | Q(booking__property__host=user)).distinct()
        return Payment.objects.none()

    def get_permissions(self):
        # Only the guest (user who made the booking) can create payment for their booking
        # Hosts (property owners) can view payments for their properties
        # Deletion/Update of payments usually restricted to admin or very specific roles
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated]  # User makes payment for their booking
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Highly restricted, often Admin only or specific roles.
            # For simplicity, let's deny for regular users unless they are admin
            self.permission_classes = [IsAuthenticated, IsAdminUser]  # Assuming IsAdminUser is a DRF default or custom
        else:  # list, retrieve
            self.permission_classes = [IsAuthenticated]  # Any related authenticated user can view

        return [permission() for permission in self.permission_classes]


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    # Permissions: Anyone can view reviews. Only authenticated users can create. Only review owner can update/delete.
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Set the user writing the review to the authenticated user
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsReviewOwner]  # IsReviewOwner needs to be defined
        else:  # 'list', 'retrieve', 'create'
            self.permission_classes = [IsAuthenticatedOrReadOnly]  # Allow anyone to read, auth to create

        return [permission() for permission in self.permission_classes]


# Placeholder for IsReviewOwner permission
class IsReviewOwner(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    # Permissions: Needs specific permissions from your previous messaging app.
    # Assuming IsMessageSenderOrConversationParticipant (renamed here as no Conversation model)
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Sender is the authenticated user
        serializer.save(sender=self.request.user)

    def get_queryset(self):
        # A user should only see messages they sent or received
        user = self.request.user
        if user.is_authenticated:
            return Message.objects.filter(Q(sender=user) | Q(receiver=user)).distinct()
        return Message.objects.none()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsMessageSender]  # IsMessageSender needs to be defined
        else:  # 'list', 'retrieve', 'create'
            self.permission_classes = [IsAuthenticated]  # All authenticated can view/create
        return [permission() for permission in self.permission_classes]


# Placeholder for IsMessageSender permission
class IsMessageSender(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.sender == request.user




