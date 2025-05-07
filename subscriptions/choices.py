from django.db.models import TextChoices


# 구독 상태
class StatusChoices(TextChoices):
    ACTIVE = 'active', '활성'
    PAUSED = 'paused', '일시중지'
    CANCELLED = 'cancelled', '취소'


# 구독 주기 정의
class FrequencyChoices(TextChoices):
    DAILY = 'daily', '매일 (월~금)'
    THREE_PER_WEEK = 'three_per_week', '주 3회 (월/수/금)'
    WEEKLY = 'weekly', '주 1회 (월요일)'
