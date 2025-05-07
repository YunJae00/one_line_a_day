from uuid import uuid4

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from accounts.models import User
from .choices import FrequencyChoices
from .models import Subscription, PendingSubscription
from .forms import SubscriptionForm, SubscriptionManageForm, DirectSubscriptionForm
from contents.models import Category
from .services import send_subscription_confirmation_email, \
    send_subscription_verification_email_with_token


@login_required
def subscription_list(request):
    """구독 목록 뷰"""
    subscriptions = Subscription.objects.filter(
        user=request.user
    ).select_related('category').order_by('-created_at')

    # todo: 이거 안쓰는데 일단 만들어둠 -> 아마 쓸지도?
    # 아직 구독하지 않은 카테고리 목록
    subscribed_category_ids = subscriptions.values_list('category_id', flat=True)
    available_categories = Category.objects.filter(
        is_active=True
    ).exclude(
        id__in=subscribed_category_ids
    ).order_by('name')

    context = {
        'subscriptions': subscriptions,
        'available_categories': available_categories,
    }

    return render(request, 'subscription/subscription_list.html', context)


@login_required
def subscribe(request):
    """구독 신청 뷰"""
    category_id = request.GET.get('category')
    initial_data = {}
    if category_id:
        try:
            category = Category.objects.get(id=category_id, is_active=True)
            initial_data['category'] = category.id
        except Category.DoesNotExist:
            pass

    if request.method == 'POST':
        form = SubscriptionForm(request.POST, user=request.user, initial=initial_data)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.status = 'active'
            subscription.save()

            messages.success(request, _(f'{subscription.category.name} 카테고리 구독이 완료되었습니다.'))
            return redirect('subscription:subscription_list')
    else:
        form = SubscriptionForm(user=request.user, initial=initial_data)

    context = {
        'form': form,
        'title': _('구독 신청'),
    }

    return render(request, 'subscription/subscription_form.html', context)


@login_required
def manage_subscription(request, subscription_id):
    """구독 관리 뷰"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)

    if request.method == 'POST':
        form = SubscriptionManageForm(request.POST, instance=subscription)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, _(f'{subscription.category.name} 구독 정보가 업데이트되었습니다.'))
            return redirect('subscription:subscription_list')
        else:
            messages.error(request, _('구독 정보 업데이트 중 오류가 발생했습니다.'))
    else:
        form = SubscriptionManageForm(instance=subscription)

    context = {
        'form': form,
        'subscription': subscription,
        'title': _('구독 관리'),
    }

    # 구독 관리 전용 템플릿 사용
    return render(request, 'subscription/subscription_manage.html', context)


@login_required
def cancel_subscription(request, subscription_id):
    """구독 취소 뷰"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)

    if request.method == 'POST':
        subscription.cancel()
        messages.success(request, _(f'{subscription.category.name} 구독이 취소되었습니다.'))
        return redirect('subscription:subscription_list')

    context = {
        'subscription': subscription,
    }

    return render(request, 'subscription/cancel_confirm.html', context)


@login_required
def pause_subscription(request, subscription_id):
    """구독 일시정지 뷰"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)

    if request.method == 'POST':
        subscription.pause()
        messages.success(request, _(f'{subscription.category.name} 구독이 일시정지되었습니다.'))
        return redirect('subscription:subscription_list')

    context = {
        'subscription': subscription,
    }

    return render(request, 'subscription/pause_confirm.html', context)


@login_required
def activate_subscription(request, subscription_id):
    """구독 활성화 뷰"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)

    if request.method == 'POST':
        subscription.activate()
        messages.success(request, _(f'{subscription.category.name} 구독이 활성화되었습니다.'))
        return redirect('subscription:subscription_list')

    context = {
        'subscription': subscription,
    }

    return render(request, 'subscription/activate_confirm.html', context)


@require_POST
def direct_subscribe(request):
    """로그인 없이 이메일만으로 구독 신청 처리"""
    form = DirectSubscriptionForm(request.POST)

    if form.is_valid():
        email = form.cleaned_data['email']
        category = form.cleaned_data['category']
        preferred_time = form.cleaned_data['preferred_time']
        frequency = form.cleaned_data.get('frequency', 'daily')

        try:
            # 이미 대기 중인 구독 신청이 있는지 확인
            existing_pending = PendingSubscription.objects.filter(
                email=email,
                category=category
            ).exists()

            if existing_pending:
                return JsonResponse({
                    'success': False,
                    'message': '이미 처리 중인 구독 신청이 있습니다. 이메일을 확인해주세요.'
                })

            # 사용자 확인 또는 생성
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'is_passwordless': True,
                    'email_verified': False,
                    'verification_token': uuid4(),
                }
            )

            # 이미 존재하는 사용자지만 인증이 안된 경우
            if not created and not user.email_verified:
                user.verification_token = uuid4()  # 토큰 재생성
                user.save(update_fields=['verification_token'])

            # 이미 인증된 사용자인 경우, 이미 해당 카테고리를 구독 중인지 확인
            if not created and user.email_verified:
                existing = Subscription.objects.filter(
                    user=user,
                    category=category,
                    status__in=['active', 'paused']
                ).exists()

                if existing:
                    return JsonResponse({
                        'success': False,
                        'message': '이미 구독 중인 카테고리입니다.'
                    })

            subscription_token = uuid4()  # 구독별 고유 토큰

            # 인증 대기 중인 구독 정보 생성
            pending = PendingSubscription.objects.create(
                email=email,
                category=category,
                preferred_time=preferred_time,
                frequency=frequency,  # 폼에서 가져온 주기 사용
                verification_token=subscription_token  # 고유 토큰 사용
            )

            frequency_display = dict(FrequencyChoices.choices).get(frequency, frequency)

            # 인증 이메일 발송 - 구독별 토큰 사용
            success = send_subscription_verification_email_with_token(user, {
                'category_name': category.name,
                'preferred_time': preferred_time.strftime('%H:%M'),
                'frequency': frequency_display  # 주기 정보 추가
            }, subscription_token)  # 구독별 토큰 전달

            if success:
                # 응답 메시지
                if created or not user.email_verified:
                    message = '이메일을 확인해주세요. 인증 후 구독이 완료됩니다.'
                else:
                    message = '이메일을 확인해 구독을 완료해주세요.'

                return JsonResponse({
                    'success': True,
                    'message': message
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '이메일 발송 중 오류가 발생했습니다. 다시 시도해주세요.'
                })

        except Exception as e:
            print(e)
            return JsonResponse({
                'success': False,
                'message': '처리 중 오류가 발생했습니다. 다시 시도해주세요.'
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


def verify_subscription(request, token):
    """이메일 인증 확인 및 구독 처리 뷰"""
    try:
        # 대기 중인 구독 정보 가져오기
        pending_subscription = get_object_or_404(PendingSubscription, verification_token=token)

        # 이메일로 사용자 찾기
        user = get_object_or_404(User, email=pending_subscription.email)

        # 인증 처리 (사용자 이메일 인증 여부 확인)
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=['email_verified'])

        # 이미 구독 중인지 확인
        existing = Subscription.objects.filter(
            user=user,
            category=pending_subscription.category,
            status__in=['active', 'paused']
        ).exists()

        if not existing:
            # 구독 생성
            subscription = Subscription.objects.create(
                user=user,
                category=pending_subscription.category,
                frequency=pending_subscription.frequency,
                preferred_time=pending_subscription.preferred_time,
                status='active'
            )

            # 대기 정보 삭제
            pending_subscription.delete()

            # 구독 확인 이메일 발송
            send_subscription_confirmation_email(user, subscription)

            context = {
                'success': True,
                'email': user.email,
                'category_name': pending_subscription.category.name,
                'preferred_time': pending_subscription.preferred_time.strftime('%H:%M'),
                'frequency': pending_subscription.frequency,
            }

            return render(request, 'subscription/subscription_verified.html', context)
        else:
            # 이미 구독 중인 경우
            context = {
                'success': False,
                'message': '이미 구독 중인 카테고리입니다.',
                'email': user.email
            }
            return render(request, 'subscription/subscription_verified.html', context)

    except Exception as e:
        context = {
            'success': False,
            'message': '처리 중 오류가 발생했습니다. 다시 시도하거나 관리자에게 문의하세요.'
        }
        return render(request, 'subscription/subscription_verified.html', context)


def manage_by_uuid(request, uuid):
    """UUID로 구독 관리 뷰"""
    try:
        user = get_object_or_404(User, uuid=uuid)

        # 사용자의 구독 목록 조회
        subscriptions = Subscription.objects.filter(
            user=user
        ).select_related('category').order_by('-created_at')

        context = {
            'user': user,
            'subscriptions': subscriptions,
        }

        return render(request, 'subscription/manage_by_uuid.html', context)
    except Exception as e:
        context = {
            'success': False,
            'message': '처리 중 오류가 발생했습니다. 다시 시도하거나 관리자에게 문의하세요.'
        }
        return render(request, 'subscription/error.html', context)


def unsubscribe_by_uuid(request, uuid, subscription_id):
    """UUID로 구독 취소 뷰"""
    try:
        user = get_object_or_404(User, uuid=uuid)
        subscription = get_object_or_404(Subscription, id=subscription_id, user=user)

        if request.method == 'POST':
            # 구독 취소 처리
            subscription.status = 'canceled'
            subscription.save(update_fields=['status'])

            return render(request, 'subscription/unsubscribe_success.html', {
                'category_name': subscription.category.name
            })

        return render(request, 'subscription/unsubscribe_confirm.html', {
            'subscription': subscription,
            'subscription_uuid': uuid
        })
    except Exception as e:
        return render(request, 'subscription/error.html', {
            'message': '구독 취소 처리 중 오류가 발생했습니다. 다시 시도하거나 관리자에게 문의하세요.'
        })


@require_POST
def pause_direct_subscription(request, uuid, subscription_id):
    """구독 일시정지 처리"""
    try:
        user = get_object_or_404(User, uuid=uuid)
        subscription = get_object_or_404(Subscription, id=subscription_id, user=user)

        subscription.status = 'paused'
        subscription.save(update_fields=['status'])

        return redirect('subscription:manage_by_uuid', uuid=uuid)
    except Exception as e:
        return render(request, 'subscription/error.html', {
            'message': '처리 중 오류가 발생했습니다. 다시 시도하거나 관리자에게 문의하세요.'
        })


@require_POST
def resume_direct_subscription(request, uuid, subscription_id):
    """구독 재개 처리"""
    try:
        user = get_object_or_404(User, uuid=uuid)
        subscription = get_object_or_404(Subscription, id=subscription_id, user=user)

        subscription.status = 'active'
        subscription.save(update_fields=['status'])

        return redirect('subscription:manage_by_uuid', uuid=uuid)
    except Exception as e:
        return render(request, 'subscription/error.html', {
            'message': '처리 중 오류가 발생했습니다. 다시 시도하거나 관리자에게 문의하세요.'
        })
