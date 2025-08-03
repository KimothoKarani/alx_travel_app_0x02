from rest_framework.routers import DefaultRouter
from .views import (UserViewSet, BookingViewSet, PaymentViewSet,
                    ReviewViewSet, MessageViewSet, PropertyViewSet)
#Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'properties', PropertyViewSet, basename='properties')
router.register(r'bookings', BookingViewSet, basename='bookings')
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'messages', MessageViewSet, basename='messages')


#The API URLS are now automatically determined by the router
urlpatterns = router.urls