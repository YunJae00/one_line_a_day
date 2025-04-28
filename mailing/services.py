import datetime
from datetime import timedelta

from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from contents.models import DailyContent
from mailing.choices import StatusChoices
from mailing.models import DailyEmail, EmailLog, SampleEmailLog
from mailing.utils import get_appropriate_template, render_template, send_email
from one_day import settings
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


def send_latest_email_sample(email_address, category_id, request_ip=None):
    """가장 최근의 DailyEmail을 즉시 발송"""
    try:
        # 이미 샘플을 받은 적이 있는지 확인
        existing_sample = SampleEmailLog.objects.filter(
            recipient_email=email_address,
            category_id=category_id,
            status=StatusChoices.SENT
        ).exists()

        if existing_sample:
            return False, "이미 해당 카테고리의 하루 한 줄을 받으셨습니다."

        # 가장 최근 DailyEmail 조회
        daily_email = DailyEmail.objects.filter(
            daily_content__category_id=category_id
        ).order_by('-email_date').first()

        if not daily_email:
            return False, "해당 카테고리의 콘텐츠가 없습니다."

        # 이메일 발송
        subject = f"[미리보기] {daily_email.subject}"
        # CTA 추가
        signup_url = f"{settings.SITE_URL}/accounts/register/"
        cta_html = f"""
        <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; text-align: center;">
            <h3 style="margin-bottom: 10px;">매일 이런 지식을 받아보고 싶으신가요?</h3>
            <p style="margin-bottom: 15px;">하루 한 줄로 꾸준히 성장하세요!</p>
            <a href="{signup_url}" style="display: inline-block; background-color: #4288EE; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                구독하기
            </a>
            <p style="margin-top: 10px; font-size: 12px; color: #6c757d;">언제든 구독 취소가 가능합니다.</p>
        </div>
        """

        # HTML 컨텐츠에 CTA 추가
        html_content_with_cta = daily_email.html_content + cta_html

        email = EmailMultiAlternatives(
            subject=subject,
            body=daily_email.text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_address]
        )
        email.attach_alternative(html_content_with_cta, "text/html")
        email.send(fail_silently=False)

        # 샘플 이메일 로그 생성
        SampleEmailLog.objects.create(
            daily_email=daily_email,
            category_id=category_id,
            recipient_email=email_address,
            subject=subject,
            status=StatusChoices.SENT,
            ip_address=request_ip
        )

        return True, "오늘의 하루 한 줄이 발송되었습니다. 이메일 및 스팸메일함을 확인해주세요!"

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send sample email: {str(e)}", exc_info=True)

        # 실패 로그 기록
        SampleEmailLog.objects.create(
            daily_email=daily_email if 'daily_email' in locals() else None,
            category_id=category_id,
            recipient_email=email_address,
            subject=f"[미리보기] 발송 실패",
            status=StatusChoices.FAILED,
            error_message=str(e),
            ip_address=request_ip
        )

        return False, "이메일 발송 중 오류가 발생했습니다."
