"""
URL configuration for one_day project.

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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from one_day import settings
from one_day.settings import get_env_variable

admin_url = get_env_variable('ADMIN_URL')

urlpatterns = [
    path(admin_url, admin.site.urls),
    # 앱 URL 연결
    path('accounts/', include('accounts.urls')),
    path('subscription/', include('subscriptions.urls')),

    # 메인 페이지
    path('', TemplateView.as_view(template_name='common/home.html'), name='home'),
]

# 개발 환경에서 정적 파일 제공
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
