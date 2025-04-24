import os
import django
import json
import logging

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
