import datetime
from datetime import timedelta

from django.utils import timezone

from contents.models import DailyContent
from mailing.choices import StatusChoices
from mailing.models import DailyEmail, EmailLog
from mailing.utils import get_appropriate_template, render_template, send_email
from subscriptions.models import Subscription

# todo: 시간 좀 정리 필요할 듯

# cron 기준 다음 날의 내용 생성
def prepare_daily_content():
    utc_now = timezone.now() + datetime.timedelta(days=1)
    korean_now = utc_now + datetime.timedelta(hours=9)

    daily_contents = DailyContent.objects.filter(
        scheduled_date=korean_now.date(),
        is_sent=False
    ).select_related('category')

    for content in daily_contents:
        template = get_appropriate_template(content)

        # 템플릿과 콘텐츠 결합하여 DailyEmail 생성
        DailyEmail.objects.create(
            daily_content=content,
            template=template,
            subject=render_template(template.subject, content),
            html_content=render_template(template.html_content, content),
            text_content=render_template(template.text_content, content),
            email_date=utc_now
        )


# 매 시간 50분에 실행 - 이메일 로그 생성
def prepare_email_logs():
    utc_now = timezone.now()
    korean_now = utc_now + datetime.timedelta(hours=9)

    # 다음 시간 계산 (자정 넘어가는 경우 고려)
    next_hour_utc = (utc_now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    next_hour_korean = (korean_now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    # 다음 시간대에 이메일을 받을 구독 조회
    # 자정 문제 해결: 24시는 0시로 처리
    target_hour = next_hour_korean.hour

    subscriptions = Subscription.objects.filter(
        status='active',
        preferred_time__hour=target_hour
    ).select_related('user', 'category')

    # todo: 이거 좀 간단히 할 필요 있음
    # 오늘 또는 내일 날짜 결정 (자정을 넘어가는 경우 내일 날짜 사용)
    target_date = korean_now.date()
    if korean_now.hour == 23:  # 23시에 실행되면 다음날 콘텐츠를 준비
        target_date = (korean_now + timedelta(days=1)).date()

    # 오늘의 요일 - 타겟 날짜 기준으로 계산
    today_weekday = target_date.weekday()  # 0=월요일, 6=일요일

    for subscription in subscriptions:
        # 구독 주기에 따른 필터링
        should_send = False
        if subscription.frequency == 'daily':
            should_send = True
        elif subscription.frequency == 'three_per_week' and today_weekday in [0, 2, 4]:  # 월,수,금
            should_send = True
        elif subscription.frequency == 'weekly' and today_weekday == 0:  # 월요일
            should_send = True

        if not should_send:
            continue

        # 해당 카테고리의 타겟 날짜 이메일 찾기
        daily_email = DailyEmail.objects.filter(
            email_date=target_date,
            daily_content__category=subscription.category
        ).first()

        if not daily_email:
            continue

        # 이미 발송 로그가 있는지 확인
        existing_log = EmailLog.objects.filter(
            user=subscription.user,
            subscription=subscription,
            daily_email=daily_email
        ).exists()

        if existing_log:
            continue

        # 이메일 로그 생성
        EmailLog.objects.create(
            user=subscription.user,
            subscription=subscription,
            daily_email=daily_email,
            recipient_email=subscription.user.email,
            subject=daily_email.subject,
            status=StatusChoices.PENDING,
            scheduled_at=next_hour_utc
        )


# 매 시간 정각에 실행 - 이메일 발송
def send_pending_emails():
    utc_now = timezone.now()
    current_hour = utc_now.replace(minute=0, second=0, microsecond=0)

    # 현재 시간에 예약된 대기 중인 이메일 로그 조회
    pending_logs = EmailLog.objects.filter(
        status=StatusChoices.PENDING,
        scheduled_at=current_hour
    ).select_related('user', 'subscription', 'daily_email')

    for log in pending_logs:
        try:
            send_email(log)
            log.mark_as_sent()
        except Exception as e:
            log.mark_as_failed(str(e))
