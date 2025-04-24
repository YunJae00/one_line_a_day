from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import Subscription
from .forms import SubscriptionForm, SubscriptionManageForm
from contents.models import Category


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
