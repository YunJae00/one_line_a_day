from django.urls import path
from . import views

app_name = 'subscription'

urlpatterns = [
    # 구독 관리
    path('', views.subscription_list, name='subscription_list'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('manage/<int:subscription_id>/', views.manage_subscription, name='manage'),
    path('cancel/<int:subscription_id>/', views.cancel_subscription, name='cancel'),
    path('pause/<int:subscription_id>/', views.pause_subscription, name='pause'),
    path('activate/<int:subscription_id>/', views.activate_subscription, name='activate'),
]