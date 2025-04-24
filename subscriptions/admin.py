from django.contrib import admin
from django.utils import timezone

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """구독 관리자 설정"""
    list_display = ('user_email', 'category', 'status', 'frequency', 'created_at', 'is_active_subscription')
    list_filter = ('status', 'frequency', 'category')
    search_fields = ('user__email', 'category__name')
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('user', 'category')
        }),
        ('구독 설정', {
            'fields': ('status', 'frequency', 'preferred_time')
        }),
        ('구독 기간', {
            'fields': ('start_date', 'end_date')
        }),
    )

    def user_email(self, obj):
        """사용자 이메일 표시"""
        return obj.user.email

    user_email.short_description = '사용자 이메일'

    def is_active_subscription(self, obj):
        """활성 구독 여부 확인"""
        if obj.status != 'active':
            return False

        today = timezone.now().date()
        if today < obj.start_date:
            return False
        if obj.end_date and today > obj.end_date:
            return False

        return True

    is_active_subscription.boolean = True
    is_active_subscription.short_description = '활성 구독'

    def get_queryset(self, request):
        """관계 필드 미리 로드"""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'category')
