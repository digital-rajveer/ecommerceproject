from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'id': 'id_username',
            'placeholder': 'Username',
            'autocomplete': 'username',
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'id': 'id_email',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'id': 'id_password1',
            'placeholder': 'Password',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'id': 'id_password2',
            'placeholder': 'Confirm Password',
            'autocomplete': 'new-password',
        })


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'id': 'id_login_username',
            'placeholder': 'Username or email',
            'autocomplete': 'username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'id': 'id_login_password',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
