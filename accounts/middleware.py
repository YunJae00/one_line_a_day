from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.urls import reverse


# todo: 이거 사용 검토... 쥐쌤을 믿지 말자
class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 세션 만료 파라미터가 URL에 있는지 확인
        if 'session_expired' in request.GET and request.path.startswith(reverse('accounts:login')):
            messages.info(request, _('로그인 세션이 만료되었습니다. 다시 로그인해주세요.'))

            request.session.modified = True

        # 인증된 사용자인 경우 마지막 활동 시간 업데이트
        if request.user.is_authenticated:
            request.session['last_activity'] = timezone.now().isoformat()

        # 세션이 있고 last_activity 값이 있는데 인증되지 않은 경우는 세션 만료로 처리
        elif not request.user.is_authenticated and 'last_activity' in request.session:
            if not request.path.startswith(reverse('accounts:login')):
                del request.session['last_activity']

                # 로그인 페이지로 리다이렉트
                return redirect(f"{reverse('accounts:login')}?session_expired=1&next={request.path}")

        response = self.get_response(request)
        return response
