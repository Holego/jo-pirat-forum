from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Post, Profile, Topic


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class BanAwareAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if getattr(user, 'profile', None) and user.profile.is_banned:
            raise ValidationError('Ваш аккаунт заблокирован на этом форуме.', code='banned')


class NewTopicForm(forms.ModelForm):
    body = forms.CharField(widget=forms.Textarea(attrs={'rows': 8}), label='Сообщение')

    class Meta:
        model = Topic
        fields = ['title', 'project_url']
        labels = {'title': 'Заголовок темы', 'project_url': 'Ссылка на проект (необязательно)'}


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['body']
        labels = {'body': ''}
        widgets = {'body': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Ваш ответ...'})}


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'website', 'github']
        labels = {
            'avatar': 'Аватар',
            'bio': 'О себе',
            'website': 'Сайт / портфолио',
            'github': 'GitHub',
        }
        widgets = {'bio': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Пара слов о себе...'})}
