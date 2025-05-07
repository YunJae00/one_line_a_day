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

    path('direct-subscribe/', views.direct_subscribe, name='direct_subscribe'),
    path('verify/<uuid:token>/', views.verify_subscription, name='verify_subscription'),
    path('manage/<uuid:uuid>/', views.manage_by_uuid, name='manage_by_uuid'),
    path('unsubscribe/<uuid:uuid>/<int:subscription_id>/', views.unsubscribe_by_uuid, name='unsubscribe_by_uuid'),
    path('pause-subscription/<uuid:uuid>/<int:subscription_id>/', views.pause_direct_subscription, name='pause_subscription'),
    path('resume-subscription/<uuid:uuid>/<int:subscription_id>/', views.resume_direct_subscription, name='resume_subscription'),
]