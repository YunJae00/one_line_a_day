from django.db.models import TextChoices


# todo: 일단 나중을 위해 만들어놨는데 삭제 고려 필요...
# 템플릿 유형
class TemplateTypeChoices(TextChoices):
    DAILY_CONTENT = 'daily_content', '일일 콘텐츠'
    WELCOME = 'welcome', '가입 환영'
    VERIFICATION = 'verification', '이메일 인증'


# 메일 상태
class StatusChoices(TextChoices):
    PENDING = 'pending', '대기 중'
    SENT = 'sent', '발송됨'
    BOUNCED = 'bounced', '반송됨'
    FAILED = 'failed', '실패'


# 체험 구독 상태
class TrialStatusChoices(TextChoices):
    ACTIVE = 'active', '활성'
    COMPLETED = 'completed', '완료됨'
    CANCELLED = 'cancelled', '취소됨'
    CONVERTED = 'converted', '정규 구독으로 전환됨'
