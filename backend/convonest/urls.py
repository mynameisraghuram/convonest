"""
URL configuration for convonest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# backend/convonest/urls.py
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),

    # Public webhook (Meta calls this)
    path("webhooks/", include("apps.webhooks.urls")),


    # API routes
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/contacts/", include("apps.contacts.urls")),
    path("api/messaging/", include("apps.messaging.urls")),
    path("api/templates/", include("apps.templates.urls")),
    path("api/whatsapp/", include("apps.whatsapp_accounts.urls")),
    path("api/core/", include("apps.core.urls")),
]
