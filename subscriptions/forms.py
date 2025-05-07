from django import forms
from django.utils.translation import gettext_lazy as _

from .choices import FrequencyChoices
from .models import Subscription
from contents.models import Category


class SubscriptionForm(forms.ModelForm):
    """구독 신청 폼"""
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        label=_('카테고리'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    frequency = forms.ChoiceField(
        choices=FrequencyChoices.choices,
        label=_('수신 주기'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    preferred_time = forms.TimeField(
        label=_('선호 시간'),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        help_text=_('이메일을 받고 싶은 시간을 선택하세요.')
    )

    class Meta:
        model = Subscription
        fields = ['category', 'frequency', 'preferred_time']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 활성화된 카테고리만 표시
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        ).order_by('name')

        # todo: 이거 당장은 안쓰는데 수정 고려 필요...
        # 요청 파라미터로 카테고리가 전달된 경우 자동 선택
        if 'initial' in kwargs and 'category' in kwargs['initial']:
            category_id = kwargs['initial']['category']
            try:
                category = Category.objects.get(id=category_id, is_active=True)
                self.fields['category'].initial = category
            except Category.DoesNotExist:
                pass

    def clean_category(self):
        """이미 구독 중인 카테고리인지 확인"""
        category = self.cleaned_data['category']

        # 이미 구독 중인 카테고리인지 확인
        if self.user and not self.instance.pk:  # 새 구독 생성 시에만 체크
            existing = Subscription.objects.filter(
                user=self.user,
                category=category,
                status__in=['active', 'paused']
            ).exists()

            if existing:
                raise forms.ValidationError(_('이미 구독 중인 카테고리입니다.'))

        return category


class DirectSubscriptionForm(forms.Form):
    """이메일만으로 구독 신청 폼"""
    email = forms.EmailField(
        label=_('이메일 주소'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '이메일을 입력해주세요'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        label=_('카테고리'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    preferred_time = forms.TimeField(
        label=_('선호 시간'),
        initial='08:00',
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    frequency = forms.ChoiceField(
        choices=FrequencyChoices.choices,
        label=_('수신 주기'),
        initial='daily',
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 활성화된 카테고리만 표시
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        ).order_by('name')


class SubscriptionManageForm(forms.ModelForm):
    """구독 관리 폼"""
    frequency = forms.ChoiceField(
        choices=FrequencyChoices.choices,
        label=_('수신 주기'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    preferred_time = forms.TimeField(
        label=_('선호 시간'),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )

    class Meta:
        model = Subscription
        fields = ['frequency', 'preferred_time']
