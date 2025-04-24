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
