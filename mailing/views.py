from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from mailing.forms import SampleEmailForm, TrialSubscriptionForm
from mailing.services import send_latest_email_sample, create_trial_subscription


def index(request):
    """메인 페이지 뷰"""
    form = SampleEmailForm()

    context = {
        'sample_form': form,
    }

    return render(request, 'common/home.html', context)


@require_POST
def sample(request):
    """샘플 이메일 발송 뷰"""
    form = SampleEmailForm(request.POST)

    if form.is_valid():
        email = form.cleaned_data['email']
        category = form.cleaned_data['category']

        # IP 주소 가져오기
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        success, message = send_latest_email_sample(email, category.id, ip_address)

        return JsonResponse({
            'success': success,
            'message': message
        })
    else:
        # 에러 메시지 수집
        errors = []
        for field, error_list in form.errors.items():
            for error in error_list:
                errors.append(str(error))

        return JsonResponse({
            'success': False,
            'message': '입력 정보를 확인해주세요.',
            'errors': errors
        })


@require_POST
def trial_subscription(request):
    """3일 무료 체험 구독 신청 뷰"""
    form = TrialSubscriptionForm(request.POST)

    if form.is_valid():
        email = form.cleaned_data['email']
        category = form.cleaned_data['category']

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        success, message = create_trial_subscription(email, category, ip_address)

        return JsonResponse({
            'success': success,
            'message': message
        })
    else:
        # 에러 메시지 수집
        errors = []
        for field, error_list in form.errors.items():
            for error in error_list:
                errors.append(str(error))

        return JsonResponse({
            'success': False,
            'message': '입력 정보를 확인해주세요.',
            'errors': errors
        })