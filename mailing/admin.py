from django.contrib import admin
from django.utils.html import format_html

from .models import EmailTemplate, DailyEmail, EmailLog


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
