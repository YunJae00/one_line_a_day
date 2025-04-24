from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class RegisterForm(UserCreationForm):
    """회원가입 폼"""
    email = forms.EmailField(
        label=_('이메일'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '이메일 주소'})
    )
    password1 = forms.CharField(
        label=_('비밀번호'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'}),
        help_text=_('8자 이상의 영문, 숫자 조합으로 입력해주세요.'),
    )
    password2 = forms.CharField(
        label=_('비밀번호 확인'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '비밀번호 확인'}),
        help_text=_('비밀번호를 다시 입력하세요.'),
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    # todo: 어찌할까...
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 필드별 오류 메시지 재정의
        self.fields['password1'].error_messages.update({
            'required': _('비밀번호를 입력해주세요.'),
        })
        self.fields['password2'].error_messages.update({
            'required': _('비밀번호 확인을 입력해주세요.'),
        })

    def clean_email(self):
        """이메일 중복 확인"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('이미 사용 중인 이메일입니다.'))
        return email


class CustomLoginForm(AuthenticationForm):
    """로그인 폼"""
    username = forms.EmailField(
        label=_('이메일'),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '이메일 주소'})
    )
    password = forms.CharField(
        label=_('비밀번호'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'}),
    )

    error_messages = {
        'invalid_login': _(
            "이메일 주소 또는 비밀번호가 올바르지 않습니다."
        ),
        'inactive': _("이 계정은 비활성화 되었습니다."),
    }


class CustomPasswordChangeForm(PasswordChangeForm):
    """비밀번호 변경 폼"""
    old_password = forms.CharField(
        label=_('현재 비밀번호'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '현재 비밀번호'}),
    )
    new_password1 = forms.CharField(
        label=_('새 비밀번호'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '새 비밀번호'}),
        help_text=_('8자 이상의 영문, 숫자 조합으로 입력해주세요.'),
    )
    new_password2 = forms.CharField(
        label=_('새 비밀번호 확인'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '새 비밀번호 확인'}),
        help_text=_('새 비밀번호를 다시 입력하세요.'),
    )
