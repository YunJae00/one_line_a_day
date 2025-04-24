from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # 회원가입 및 인증
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),

    # 비밀번호 관리
    path('password/reset-temp/', views.reset_password, name='reset_password'),
    path('password/change/', views.change_password, name='change_password'),

    # 프로필
    path('profile/', views.profile, name='profile'),
]