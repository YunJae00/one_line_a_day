from django.db import models
from django.conf import settings
from django.utils import timezone

from contents.models import Category
from subscriptions import choices


class Subscription(models.Model):
    """
    사용자 구독 정보 모델
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="사용자"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="카테고리"
    )

    # 구독 설정
    status = models.CharField(
        max_length=10,
        choices=choices.StatusChoices.choices,
        default=choices.StatusChoices.ACTIVE,
        verbose_name="상태"
    )
    frequency = models.CharField(
        max_length=15,
        choices=choices.FrequencyChoices.choices,
        default=choices.FrequencyChoices.DAILY,
        verbose_name="수신 주기"
    )

    # 수신 시간 설정 (기본 오전 8시)
    preferred_time = models.TimeField(
        default=timezone.datetime.strptime('08:00', '%H:%M').time(),
        verbose_name="선호 시간"
    )

    # todo: 이거 일단은 안씀
    # 시작일/종료일 (종료일은 선택사항)
    start_date = models.DateField(default=timezone.now, verbose_name="시작일")
    end_date = models.DateField(null=True, blank=True, verbose_name="종료일")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "구독"
        db_table = "subscriptions"

    def __str__(self):
        return f"{self.user.email} - {self.category} ({self.get_status_display()})"

    @property
    def is_active(self):
        """구독이 활성 상태인지 확인"""
        return self.status == 'active'

    def activate(self):
        """구독 활성화"""
        self.status = 'active'
        self.save(update_fields=['status', 'updated_at'])

    def pause(self):
        """구독 일시 중지"""
        self.status = 'paused'
        self.save(update_fields=['status', 'updated_at'])

    def cancel(self):
        """구독 취소"""
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])

    def should_send_today(self):
        """오늘 이메일을 보내야 하는지 확인"""
        if not self.is_active:
            return False

        today = timezone.now().date()
        weekday = today.weekday()  # 0=월요일, 6=일요일

        # 시작일/종료일 체크
        if today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False

        # 주기에 따른 전송 여부 확인
        if self.frequency == 'daily':
            return True
        elif self.frequency == 'three_per_week':
            # 월(0), 수(2), 금(4)에만 전송
            return weekday in [0, 2, 4]
        elif self.frequency == 'weekly':
            # 월요일(0)에만 전송
            return weekday == 0

        return False
