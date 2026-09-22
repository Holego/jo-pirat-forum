from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Post, Topic


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class NewTopicForm(forms.ModelForm):
    body = forms.CharField(widget=forms.Textarea(attrs={'rows': 8}), label='Сообщение')

    class Meta:
        model = Topic
        fields = ['title', 'project_url']
        labels = {'title': 'Заголовок темы'}


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['body']
        labels = {'body': ''}
        widgets = {'body': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Ваш ответ...'})}
