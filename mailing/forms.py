from django import forms
from django.utils.translation import gettext_lazy as _
from contents.models import Category


class SampleEmailForm(forms.Form):
    """샘플 이메일 폼"""
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        empty_label=_("카테고리 선택"),
        label=_('카테고리'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label=_('이메일'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('이메일 주소')
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 활성화된 카테고리만 표시
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        ).order_by('name')
