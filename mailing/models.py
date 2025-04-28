from django.db import models
import uuid

from accounts.models import User
from contents.models import Category, DailyContent
from mailing.choices import TemplateTypeChoices, StatusChoices
from subscriptions.models import Subscription


class EmailTemplate(models.Model):
    """
    이메일 템플릿 모델
    """
    name = models.CharField(max_length=100, verbose_name="템플릿명")
    subject = models.CharField(max_length=200, verbose_name="이메일 제목")
    html_content = models.TextField(verbose_name="HTML 내용")
    text_content = models.TextField(verbose_name="텍스트 내용")

    template_type = models.CharField(
        max_length=20,
        choices=TemplateTypeChoices.choices,
        default=TemplateTypeChoices.DAILY_CONTENT,
        verbose_name="템플릿 유형"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_templates',
        verbose_name="카테고리"
    )

    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "이메일 템플릿"
        db_table = "email_templates"

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class DailyEmail(models.Model):
    """
    발송되는 이메일의 실제 내용을 저장하는 모델
    """
    # 관계
    daily_content = models.ForeignKey(
        DailyContent,
        on_delete=models.CASCADE,
        related_name='daily_emails',
        verbose_name="일일 콘텐츠"
    )
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='daily_emails',
        verbose_name="사용 템플릿"
    )

    # 이메일 내용
    subject = models.CharField(max_length=200, verbose_name="제목")
    html_content = models.TextField(verbose_name="HTML 내용")
    text_content = models.TextField(verbose_name="텍스트 내용")

    # 날짜 및 메타데이터
    email_date = models.DateField(verbose_name="이메일 날짜")
    is_generated = models.BooleanField(default=True, verbose_name="생성 완료")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "일일 이메일"
        db_table = "daily_emails"
        ordering = ['-email_date']

    def __str__(self):
        return f"일일 이메일: {self.subject} ({self.email_date})"


class EmailLog(models.Model):
    """
    이메일 발송 로그
    """

    # 고유 식별자
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_logs',
        verbose_name="사용자"
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='email_logs',
        null=True,
        blank=True,
        verbose_name="구독"
    )
    daily_email = models.ForeignKey(
        DailyEmail,
        on_delete=models.CASCADE,
        related_name='email_logs',
        null=True,
        blank=True,
        verbose_name="일일 이메일"
    )

    # 이메일 정보
    recipient_email = models.EmailField(verbose_name="수신 이메일")
    subject = models.CharField(max_length=200, verbose_name="제목")
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name="상태"
    )

    # 오류 정보
    error_message = models.TextField(blank=True, verbose_name="오류 메시지")

    # 시간 정보
    scheduled_at = models.DateTimeField(verbose_name="예약 시간")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="발송 시간")

    # 생성 일시
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        verbose_name = "이메일 로그"
        db_table = "email_logs"
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_at']),
        ]

    def __str__(self):
        return f"{self.recipient_email} - {self.subject[:30]} ({self.get_status_display()})"

    def mark_as_sent(self):
        """이메일을 발송됨으로 표시"""
        from django.utils import timezone
        self.status = StatusChoices.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    def mark_as_failed(self, error_message):
        """이메일 발송 실패로 표시"""
        self.status = StatusChoices.FAILED
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def mark_as_bounced(self, bounce_reason):
        """이메일 반송으로 표시"""
        self.status = StatusChoices.BOUNCED
        self.error_message = bounce_reason
        self.save(update_fields=['status', 'error_message'])


class SampleEmailLog(models.Model):
    """
    샘플 이메일 발송 로그
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    daily_email = models.ForeignKey(
        DailyEmail,
        on_delete=models.CASCADE,
        related_name='sample_email_logs',
        verbose_name="일일 이메일"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='sample_email_logs',
        verbose_name="카테고리",
        null=True,
        blank=True
    )

    # 이메일 정보
    recipient_email = models.EmailField(verbose_name="수신 이메일")
    subject = models.CharField(max_length=200, verbose_name="제목")
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name="상태"
    )

    # 오류 정보
    error_message = models.TextField(blank=True, verbose_name="오류 메시지")

    # 시간 정보
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="발송 시간")

    # 추가 정보
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP 주소")

    class Meta:
        verbose_name = "샘플 이메일 로그"
        verbose_name_plural = "샘플 이메일 로그"
        db_table = "sample_email_logs"
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['recipient_email']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return f"{self.recipient_email} - {self.subject[:30]} ({self.get_status_display()})"
