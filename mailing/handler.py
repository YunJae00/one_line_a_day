import os
import django
import json
import logging

from mailing.choices import StatusChoices
from mailing.models import EmailLog

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def django_setup():
    """Django 환경 초기화"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'one_day.settings')
    django.setup()


def daily_content_handler(event, context):
    """
    다음 날 발송할 이메일 준비
    """
    django_setup()

    from mailing.services import prepare_daily_content

    logger.info("Starting daily content preparation")
    result = prepare_daily_content()

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }


def prepare_email_logs_handler(event, context):
    """
    매 시간 50분에 실행
    다음 시간에 발송할 이메일 로그를 준비
    """
    django_setup()

    from mailing.services import prepare_email_logs

    logger.info("Starting email logs preparation")
    result = prepare_email_logs()

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }


def send_pending_emails_handler(event, context):
    """
    매 시간 정각에 실행
    해당 시간에 예약된 이메일을 발송
    """
    django_setup()

    from mailing.services import send_pending_emails

    logger.info("Starting pending emails sending")
    result = send_pending_emails()

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }


def sns_bounce_handler(event, context):
    """
    SNS로부터 받은 바운스 알림 처리
    """
    django_setup()
    import json

    logger.info(f"Received SNS event: {event}")

    for record in event.get('Records', []):
        sns_message = json.loads(record['Sns']['Message'])
        notification_type = sns_message.get('notificationType')

        if notification_type == 'Bounce':
            handle_ses_bounce(sns_message)
        elif notification_type == 'Complaint':
            # 컴플레인 처리
            pass

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Processed successfully'})
    }


def handle_ses_bounce(bounce_notification):
    bounce_info = bounce_notification.get('bounce', {})
    recipients = bounce_info.get('bouncedRecipients', [])
    bounce_type = bounce_info.get('bounceType')
    bounce_subtype = bounce_info.get('bounceSubType')

    for recipient in recipients:
        email = recipient.get('emailAddress')
        bounce_reason = recipient.get('diagnosticCode', f'Bounce Type: {bounce_type}, SubType: {bounce_subtype}')

        # SENT 상태인 이메일 로그 찾기 (수정됨)
        logs = EmailLog.objects.filter(
            recipient_email=email,
            status=StatusChoices.SENT  # BOUNCED가 아닌 SENT 찾기
        ).order_by('-sent_at')

        if logs.exists():
            log = logs.first()
            log.mark_as_bounced(bounce_reason)
            logger.info(f"Marked email as bounced: {email}")
