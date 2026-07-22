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
from django.conf import settings
from django.views.static import serve as static_serve
from analyzer.views import FrontendView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('api/', include('accounts.urls')),
    path('api/', include('analyzer.urls')),
    # Serve Vite-built assets (JS, CSS, images from /assets/*)
    re_path(r'^assets/(?P<path>.*)$', static_serve,
            {'document_root': str(settings.STATIC_ROOT / 'assets')}),
    # Serve other root-level Vite files (favicon, etc.)
    re_path(r'^(?P<path>vite\.svg)$', static_serve,
            {'document_root': str(settings.STATIC_ROOT)}),
    # SPA catch-all: any non-API/admin/account/assets path serves index.html
    re_path(r'^(?!api/|admin/|accounts/|assets/|vite\.svg).*$', FrontendView.as_view(), name='spa-catchall'),
]
