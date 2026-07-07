"""
URL configuration for chessslizer project.

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
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from analyzer.views import FrontendView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('api/', include('accounts.urls')),
    path('api/', include('analyzer.urls')),
    # SPA catch-all: any non-API/admin/accounts path serves index.html
    # so react-router can handle client-side routing.
    re_path(r'^(?!api/|admin/|accounts/).*$', FrontendView.as_view(), name='spa-catchall'),
]
