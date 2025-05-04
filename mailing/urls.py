from django.urls import path
from . import views

app_name = 'mailing'

urlpatterns = [
    path('sample/', views.sample, name='sample'),
    path('trial/', views.trial_subscription, name='trial'),
]