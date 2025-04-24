from uuid import uuid4
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """사용자 매니저"""

    def create_user(self, email, password=None, **extra_fields):
        """일반 사용자 생성"""
        if not email:
            raise ValueError('이메일은 필수입니다')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """관리자 사용자 생성"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('관리자는 is_staff=True가 필요합니다')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('관리자는 is_superuser=True가 필요합니다')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """사용자 모델"""

    # 기본 식별 필드
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False, verbose_name="UUID")
    email = models.EmailField(unique=True, verbose_name="이메일")

    # 상태 필드
    email_verified = models.BooleanField(default=False, verbose_name="이메일 인증 여부")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    is_staff = models.BooleanField(default=False, verbose_name="관리자 여부")
    is_superuser = models.BooleanField(default=False, verbose_name="슈퍼유저 여부")

    # 인증 관련 필드
    verification_token = models.UUIDField(default=uuid4, editable=False, null=True, blank=True)

    # 시간 정보
    created_at = models.DateTimeField(default=timezone.now, verbose_name="가입 일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 일시")

    # UserManager 설정
    objects = UserManager()

    # 인증에 사용할 필드 지정
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "사용자"
        db_table = "users"

    def __str__(self):
        return self.email

    def verify_email(self):
        """이메일 인증 처리"""
        self.email_verified = True
        self.verification_token = None
        self.save(update_fields=['email_verified', 'verification_token'])

    def generate_new_verification_token(self):
        """새 인증 토큰 생성"""
        self.verification_token = uuid4()
        self.save(update_fields=['verification_token'])
