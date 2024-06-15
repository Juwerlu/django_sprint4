from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm

from blog.models import Comment, Post, User


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = (
            'text',
        )
        widgets = {'text': forms.Textarea(attrs={'rows': settings.ROWS})}


class ProfileForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email'
        )
