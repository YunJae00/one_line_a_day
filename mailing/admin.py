from django.contrib import admin
from django.utils.html import format_html

from .choices import StatusChoices
from .models import EmailTemplate, DailyEmail, EmailLog, SampleEmailLog, TrialSubscription, TrialEmailLog


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """이메일 템플릿 관리자 설정"""
    list_display = ('name', 'template_type', 'category', 'is_active', 'updated_at')
    list_filter = ('template_type', 'is_active', 'category')
    search_fields = ('name', 'subject', 'html_content')

    fieldsets = (
        (None, {
            'fields': ('name', 'template_type', 'category', 'is_active')
        }),
        ('이메일 내용', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
    )


@admin.register(DailyEmail)
class DailyEmailAdmin(admin.ModelAdmin):
    """일일 이메일 관리자 설정"""
    list_display = ('subject', 'daily_content', 'email_date', 'is_generated', 'created_at')
    list_filter = ('is_generated', 'email_date', 'daily_content__category')
    search_fields = ('subject', 'html_content', 'daily_content__title')
    date_hierarchy = 'email_date'

    fieldsets = (
        (None, {
            'fields': ('daily_content', 'template', 'email_date', 'is_generated')
        }),
        ('이메일 내용', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
    )

    def get_queryset(self, request):
        """관계 필드 미리 로드"""
        queryset = super().get_queryset(request)
        return queryset.select_related('daily_content', 'template')


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """이메일 로그 관리자 설정"""
    list_display = ('recipient_email', 'subject_preview', 'status', 'scheduled_at', 'sent_at')
    list_filter = ('status', 'scheduled_at', 'sent_at')
    search_fields = ('recipient_email', 'subject', 'error_message')
    date_hierarchy = 'scheduled_at'
    readonly_fields = ('uuid', 'user', 'subscription', 'daily_email', 'recipient_email',
                       'subject', 'status', 'error_message', 'scheduled_at', 'sent_at')

    fieldsets = (
        (None, {
            'fields': ('uuid', 'user', 'subscription', 'daily_email')
        }),
        ('이메일 정보', {
            'fields': ('recipient_email', 'subject')
        }),
        ('상태 정보', {
            'fields': ('status', 'scheduled_at', 'sent_at')
        }),
        ('오류 정보', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )

    def subject_preview(self, obj):
        """제목 미리보기"""
        return format_html('<span title="{}">{}</span>',
                           obj.subject,
                           obj.subject[:30] + '...' if len(obj.subject) > 30 else obj.subject)

    subject_preview.short_description = '제목'

    def has_add_permission(self, request):
        """추가 권한 제한"""
        return False

    def has_delete_permission(self, request, obj=None):
        """삭제 권한 제한"""
        return False

    def get_queryset(self, request):
        """관계 필드 미리 로드"""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'subscription', 'daily_email')


@admin.register(SampleEmailLog)
class SampleEmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'subject', 'status', 'sent_at', 'ip_address')
    list_filter = ('status', 'sent_at')
    search_fields = ('recipient_email', 'subject', 'ip_address')
    readonly_fields = ('uuid', 'sent_at')

    fieldsets = (
        ('이메일 정보', {
            'fields': ('recipient_email', 'subject', 'daily_email')
        }),
        ('상태', {
            'fields': ('status', 'error_message')
        }),
        ('메타 정보', {
            'fields': ('uuid', 'sent_at', 'ip_address')
        }),
    )


@admin.register(TrialSubscription)
class TrialSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'category', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'category', 'start_date')
    search_fields = ('email',)
    date_hierarchy = 'created_at'
    readonly_fields = ('uuid', 'created_at')
    actions = ['mark_as_completed', 'mark_as_cancelled', 'mark_as_converted']

    def mark_as_completed(self, request, queryset):
        for trial in queryset:
            trial.complete()
        self.message_user(request, f"{queryset.count()}개의 체험 구독이 완료 상태로 변경되었습니다.")
    mark_as_completed.short_description = "선택한 체험 구독을 완료 상태로 변경"

    def mark_as_cancelled(self, request, queryset):
        for trial in queryset:
            trial.cancel()
        self.message_user(request, f"{queryset.count()}개의 체험 구독이 취소 상태로 변경되었습니다.")
    mark_as_cancelled.short_description = "선택한 체험 구독을 취소 상태로 변경"

    def mark_as_converted(self, request, queryset):
        for trial in queryset:
            trial.convert()
        self.message_user(request, f"{queryset.count()}개의 체험 구독이 전환 상태로 변경되었습니다.")
    mark_as_converted.short_description = "선택한 체험 구독을 전환 상태로 변경"


@admin.register(TrialEmailLog)
class TrialEmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'subject', 'status', 'day_number', 'scheduled_at', 'sent_at')
    list_filter = ('status', 'day_number')
    search_fields = ('recipient_email', 'subject')
    date_hierarchy = 'scheduled_at'
    readonly_fields = ('uuid', 'sent_at')
    actions = ['resend_failed_emails']

    def resend_failed_emails(self, request, queryset):
        from mailing.services import send_trial_email

        success_count = 0
        for log in queryset.filter(status=StatusChoices.FAILED):
            if send_trial_email(log):
                success_count += 1

        self.message_user(request, f"{success_count}개의 이메일이 재발송되었습니다.")
    resend_failed_emails.short_description = "실패한 이메일 재발송"
