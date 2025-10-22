from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Transaction, Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type']

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['category', 'description', 'amount']

class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким именем уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким адресом электронной почты уже существует.")
        return email


class SharedAccountForm(forms.Form):
    email = forms.EmailField(label='Email пользователя', required=True)
    access_data = forms.MultipleChoiceField(
        label='Выберите доступные данные',
        choices=[
            ('profile', 'Профиль пользователя'),
            ('settings', 'Настройки'),
            ('dashboard', 'Личный кабинет'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )