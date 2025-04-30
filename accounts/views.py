from uuid import uuid4
import random
import string
import logging

from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import boto3
from botocore.exceptions import ClientError

from .forms import RegisterForm, CustomLoginForm, CustomPasswordChangeForm

User = get_user_model()


def register(request):
    """회원가입 뷰"""
    if request.user.is_authenticated:
        return redirect('subscription:subscription_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # 이메일 인증 전에도 계정은 활성화 상태
            user.email_verified = False  # 인증 전이므로 False로 설정
            user.verification_token = uuid4()
            user.save()

            # 이메일 인증 메일 발송
            send_verification_email(user)

            messages.success(request, _('회원가입이 완료되었습니다. 이메일 및 스팸메일함을 확인하여 인증을 완료해주세요.'))
            return redirect('accounts:login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request, token):
    """이메일 인증 뷰"""
    try:
        user = get_object_or_404(User, verification_token=token)

        if not user.email_verified:
            user.verify_email()
            # 인증 후 웰컴 메일 발송
            send_welcome_email(user)
            messages.success(request, _('이메일 인증이 완료되었습니다. 로그인 후 구독을 설정해주세요.'))
        else:
            messages.info(request, _('이미 인증된 이메일입니다.'))

        return render(request, 'accounts/verification_complete.html')
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"이메일 인증 오류: {e}")

        # 사용자에게 보여줄 오류 메시지
        messages.error(request, _('이메일 인증 중 오류가 발생했습니다. 다시 시도하거나 관리자에게 문의하세요.'))
        return render(request, 'accounts/login.html', status=500)  # 오류 페이지가 없으면 로그인 페이지로


def send_verification_email(user):
    """이메일 인증 메일 발송 함수"""
    verification_link = reverse('accounts:verify_email', kwargs={'token': user.verification_token})
    verification_url = f"{settings.SITE_URL}{verification_link}"

    html_message = render_to_string('accounts/email/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })

    subject = str(_('[하루 한 줄] 이메일 인증을 완료해주세요'))
    message = str(_('이메일 인증을 완료하려면 다음 링크를 클릭하세요: ')) + verification_url

    # SES 클라이언트 직접 생성
    try:
        # SES 클라이언트 직접 생성
        ses_client = boto3.client(
            'ses',
            region_name=settings.AWS_SES_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # SES API를 사용하여 이메일 직접 전송
        response = ses_client.send_email(
            Source=settings.DEFAULT_FROM_EMAIL,
            Destination={
                'ToAddresses': [user.email],
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
    except ClientError as e:
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


def send_welcome_email(user):
    """회원가입 웰컴 이메일 발송 함수"""
    html_message = render_to_string('accounts/email/welcome_email.html', {
        'user': user,
    })

    subject = str(_('[하루 한 줄] 회원가입을 환영합니다'))
    message = str(_('하루 한 줄 서비스에 가입해 주셔서 감사합니다. 매일 아침, 유용한 지식과 인사이트를 이메일로 받아보실 수 있습니다.'))

    try:
        # SES 클라이언트 직접 생성
        ses_client = boto3.client(
            'ses',
            region_name=settings.AWS_SES_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # SES API를 사용하여 이메일 직접 전송
        response = ses_client.send_email(
            Source=settings.DEFAULT_FROM_EMAIL,
            Destination={
                'ToAddresses': [user.email],
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
    except ClientError as e:
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


@login_required
def profile(request):
    """사용자 프로필 뷰"""
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def change_password(request):
    """비밀번호 변경 뷰"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # 비밀번호 변경 후 로그인 상태 유지 (세션 유지로)
            update_session_auth_hash(request, user)
            messages.success(request, _('비밀번호가 성공적으로 변경되었습니다.'))
            return redirect('accounts:profile')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    # 커스텀 폼 사용하기로..
    # todo: 기존 폼 사용 검토
    form_class = CustomLoginForm

    def get(self, request, *args, **kwargs):
        # todo: 이거 다시 체크 필요
        if 'next' in request.GET and not request.user.is_authenticated:
            messages.info(request, _('로그인 세션이 만료되었습니다. 다시 로그인해주세요.'))

        return super().get(request, *args, **kwargs)


@login_required
def logout_view(request):
    """로그아웃 확인 뷰"""
    if not request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        # todo: 데이터베ㅣㅇ스 세션 삭제 검토
        session_key = request.session.session_key
        logout(request)

        # 데이터베이스에서 세션 레코드 완전히 삭제
        from django.contrib.sessions.models import Session
        try:
            if session_key:
                Session.objects.filter(session_key=session_key).delete()
        except Exception:
            pass

        return redirect('home')

    return render(request, 'accounts/logout.html')


def reset_password(request):
    """임시 비밀번호 발급 및 이메일 발송 뷰"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)

            # 임시 비밀번호 생성 (영문 대소문자, 숫자 포함 12자)
            temp_password = ''.join(random.choices(
                string.ascii_uppercase + string.ascii_lowercase + string.digits,
                k=12
            ))

            # 사용자 비밀번호 변경
            user.set_password(temp_password)
            user.save()

            # 이메일 발송
            send_temp_password_email(user, temp_password)

            messages.success(request, _('임시 비밀번호가 이메일로 발송되었습니다. 이메일 및 스팸메일함을 확인해주세요.'))
            return redirect('accounts:login')

        except User.DoesNotExist:
            messages.error(request, _('등록되지 않은 이메일 주소입니다.'))

    return render(request, 'accounts/reset_password.html')


def send_temp_password_email(user, temp_password):
    """임시 비밀번호 이메일 발송 함수"""
    html_message = render_to_string('accounts/email/temp_password_email.html', {
        'user': user,
        'temp_password': temp_password,
    })

    subject = str(_('[하루 한 줄] 임시 비밀번호 안내'))
    message = str(_('임시 비밀번호: ')) + temp_password + '\n' + str(_('로그인 후 반드시 비밀번호를 변경해주세요.'))

    try:
        # SES 클라이언트 직접 생성
        ses_client = boto3.client(
            'ses',
            region_name=settings.AWS_SES_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # SES API를 사용하여 이메일 직접 전송
        response = ses_client.send_email(
            Source=settings.DEFAULT_FROM_EMAIL,
            Destination={
                'ToAddresses': [user.email],
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
    except ClientError as e:
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
