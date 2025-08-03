"""
URL configuration for alx_travel_app project.

This file defines the main URL routing for the project, including:
- Admin panel
- API endpoints
- JWT authentication
- Auto-generated API documentation (Swagger and Redoc)
"""

from django.contrib import admin
from django.urls import path, include

# Import JWT views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# --- Import drf-spectacular views ---
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # --- Your main API endpoints ---
    path('api/', include('listings.urls')),

    # --- JWT Authentication endpoints ---
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- drf-spectacular schema and documentation URLs ---

    # Generates the OpenAPI schema (JSON or YAML format)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI documentation (interactive API tester)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Redoc UI documentation (alternative API docs view)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
