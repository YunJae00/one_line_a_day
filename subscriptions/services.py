import boto3
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


def send_subscription_verification_email_with_token(user, subscription_info=None, subscription_token=None):
    """구독 인증 이메일 발송 함수"""
    verification_link = reverse('subscription:verify_subscription', kwargs={'token': subscription_token})
    verification_url = f"{settings.SITE_URL}{verification_link}"

    # HTML 메시지 생성
    html_message = render_to_string('subscription/email/subscription_verification.html', {
        'user': user,
        'verification_url': verification_url,
        'subscription_info': subscription_info,
        'site_url': settings.SITE_URL
    })

    subject = str(_('[하루 한 줄] 이메일 인증 및 구독 완료를 위해 확인해주세요'))
    message = str(_(f'''안녕하세요!
    
하루 한 줄 구독을 신청해주셔서 감사합니다.
이메일 인증을 완료하고 구독을 시작하려면 다음 링크를 클릭하세요:
{verification_url}

감사합니다.
하루 한 줄 팀 드림'''))

    try:
        # SES 클라이언트 생성
        ses_client = boto3.client(
            'ses',
            region_name=settings.AWS_SES_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # 이메일 발송
        response = ses_client.send_email(
            Source=settings.DEFAULT_FROM_EMAIL,
            Destination={
                'ToAddresses': [user.email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': message,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': html_message,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        return True
    except Exception as e:
        # 직접 호출에 실패한 경우 Django의 이메일 백엔드 사용 시도
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            return True
        except Exception as e2:
            return False


def send_subscription_confirmation_email(user, subscription):
    """구독 확인 이메일 발송 함수"""
    # 관리 URL 생성 (subscription_uuid 사용)
    management_url = f"{settings.SITE_URL}/subscription/manage/{user.uuid}/"
    unsubscribe_url = f"{settings.SITE_URL}/subscription/unsubscribe/{user.uuid}/{subscription.id}/"

    frequency_display = subscription.get_frequency_display

    context = {
        'user': user,
        'subscription': subscription,
        'category_name': subscription.category.name,
        'preferred_time': subscription.preferred_time.strftime('%H:%M'),
        'frequency': frequency_display,
        'management_url': management_url,
        'unsubscribe_url': unsubscribe_url,
        'site_url': settings.SITE_URL
    }

    html_message = render_to_string('subscription/email/subscription_confirmation.html', context)

    subject = str(_('[하루 한 줄] 구독이 완료되었습니다'))
    text_message = str(_(f'''안녕하세요!

하루 한 줄 구독이 성공적으로 완료되었습니다.

- 카테고리: {subscription.category.name}
- 수신 시간: {subscription.preferred_time.strftime('%H:%M')}
- 수신 주기: {subscription.get_frequency_display()}

내일부터 선택하신 시간에 이메일이 발송됩니다.
구독 관리: {management_url}
구독 취소: {unsubscribe_url}

감사합니다.
하루 한 줄 팀 드림'''))

    try:
        # SES 클라이언트 생성
        ses_client = boto3.client(
            'ses',
            region_name=settings.AWS_SES_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # 이메일 발송
        response = ses_client.send_email(
            Source=settings.DEFAULT_FROM_EMAIL,
            Destination={
                'ToAddresses': [user.email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': text_message,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': html_message,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        return True
    except Exception as e:
        return False
