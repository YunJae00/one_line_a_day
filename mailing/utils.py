from django.template import Template, Context

from one_day import settings


def get_appropriate_template(content):
    """
    콘텐츠에 적합한 이메일 템플릿
    1. 해당 카테고리 전용 템플릿이 있는지 확인
    2. 없으면 기본 일일 콘텐츠 템플릿 사용
    """
    from mailing.models import EmailTemplate
    from mailing.choices import TemplateTypeChoices

    # 해당 카테고리 전용 템플릿 찾기
    template = EmailTemplate.objects.filter(
        category=content.category,
        template_type=TemplateTypeChoices.DAILY_CONTENT,
        is_active=True
    ).first()

    # 카테고리별 템플릿이 없으면 기본 템플릿 사용
    if not template:
        template = EmailTemplate.objects.filter(
            category__isnull=True,
            template_type=TemplateTypeChoices.DAILY_CONTENT,
            is_active=True
        ).first()

    return template


def render_template(template_string, content):
    """
    템플릿 문자열을 콘텐츠 데이터와 결합
    """
    from django.template import Template, Context

    # 콘텐츠 컨텍스트 생성
    context_data = {
        'content': content,
        'category': content.category,
        'site_url': settings.SITE_URL,
    }

    # 템플릿 렌더링
    template = Template(template_string)
    context = Context(context_data)

    return template.render(context)


def send_email(log):
    """
    EmailLog를 기반으로 실제 이메일을 발송
    """
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings

    try:
        daily_email = log.daily_email
        daily_content = daily_email.daily_content
        user = log.user
        subscription = log.subscription

        # todo: 이거 삭제해서 지워야하는데 일단 다른 중요한거부터...
        # 구독 관리 링크 생성
        manage_url = f"{settings.SITE_URL}/subscriptions/"
        pause_url = f"{settings.SITE_URL}/subscriptions/pause/{subscription.id}/"
        cancel_url = f"{settings.SITE_URL}/subscriptions/cancel/{subscription.id}/"

        # 추가 컨텍스트 생성
        context = {
            'user': user,
            'subscription': subscription,
            'content': daily_content,
            'category': daily_content.category,
            'manage_url': manage_url,
            'pause_url': pause_url,
            'cancel_url': cancel_url
        }

        # HTML 콘텐츠에 적용
        from django.template import Template, Context
        html_template = Template(daily_email.html_content)
        text_template = Template(daily_email.text_content)

        html_content = html_template.render(Context(context))
        text_content = text_template.render(Context(context))

        # 이메일 객체 생성
        email = EmailMultiAlternatives(
            subject=daily_email.subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            headers={'X-Log-ID': str(log.uuid)}  # 추적용 헤더 추가 todo: 이건 나중에 다시 찾아봐야함.. 일단 쓰자..
        )

        # HTML 버전 추가
        email.attach_alternative(html_content, "text/html")

        # 이메일 발송
        email.send(fail_silently=False)

        # 로그 업데이트
        log.mark_as_sent()

        # 콘텐츠 발송 표시 (같은 콘텐츠가 여러 사용자에게 발송될 수 있움)
        daily_content = daily_email.daily_content
        if not daily_content.is_sent:
            daily_content.is_sent = True
            daily_content.save(update_fields=['is_sent'])

        return True

    except Exception as e:
        # 발송 실패 시 로그 업데이트
        log.mark_as_failed(str(e))
        # 로깅
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send email: {str(e)}", exc_info=True)

        return False


def prepare_trial_cta_html(day_number, signup_url):
    """
    체험 이메일용 CTA HTML 생성
    """
    # 일반 CTA
    if day_number < 3:
        return f"""
        <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; text-align: center;">
            <h3 style="margin-bottom: 10px;">하루 한 줄, 어떠신가요?</h3>
            <p style="margin-bottom: 15px;">체험 {day_number}일차입니다. 총 3일간 매일 이런 지식을 받아보세요!</p>
            <a href="{signup_url}" style="display: inline-block; background-color: #4288EE; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                지금 가입하고 계속 받기
            </a>
            <p style="margin-top: 10px; font-size: 12px; color: #6c757d;">체험 기간은 총 3일이며, 그 이후에도 계속 받기를 원하시면 가입해주세요.</p>
        </div>
        """

    # 마지막 날 강조된 CTA
    return f"""
    <div style="margin-top: 30px; padding: 20px; background-color: #f0f7ff; border-radius: 8px; text-align: center; border: 2px solid #4288EE;">
        <h3 style="margin-bottom: 10px; color: #3070d9;">체험 마지막 날입니다!</h3>
        <p style="margin-bottom: 15px;">3일 체험이 오늘로 종료됩니다. 어떠셨나요? 계속해서 매일 새로운 지식을 받아보세요.</p>
        <a href="{signup_url}" style="display: inline-block; background-color: #4288EE; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">
            지금 가입하고 계속 받기
        </a>
        <p style="margin-top: 15px; color: #3070d9;">가입하시면 더 많은 카테고리의 지식을 선택할 수 있습니다!</p>
    </div>
    """


def render_trial_email_content(daily_email, trial, day_number):
    """
    체험 이메일 컨텐츠 렌더링
    """
    from django.conf import settings

    # 구독 링크 생성
    signup_url = f"{settings.SITE_URL}/accounts/register/"

    # 추가 컨텍스트 생성
    context = {
        'trial': trial,
        'day_number': day_number,
        'category': daily_email.daily_content.category,
        'content': daily_email.daily_content,
        'signup_url': signup_url,
        'site_url': settings.SITE_URL
    }

    # HTML 컨텐츠와 텍스트 컨텐츠 렌더링
    html_template = Template(daily_email.html_content)
    text_template = Template(daily_email.text_content)

    html_content = html_template.render(Context(context))
    text_content = text_template.render(Context(context))

    # CTA 추가
    cta_html = prepare_trial_cta_html(day_number, signup_url)
    html_content_with_cta = html_content + cta_html

    return {
        'html_content': html_content_with_cta,
        'text_content': text_content
    }
