from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Transaction, Category
import re
import datetime
from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Goal

class GoalForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0.01,
        label='Сумма (общая)'
    )
    participants = forms.CharField(
        widget=forms.Textarea(attrs={'rows':3}),
        required=False,
        label='Кто участвует (emails через запятую / ; / новую строку)',
        help_text='Например: a@example.com, b@example.com'
    )
    deadline = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Дедлайн'
    )

    class Meta:
        model = Goal
        fields = ['name', 'description', 'deadline', 'status']

    def clean_participants(self):
        raw = (self.cleaned_data.get('participants') or '').strip()
        if not raw:
            return []
        # split по запятой/точке с запятой/переносу строки
        parts = [p.strip() for p in re.split(r'[,\n;]+', raw) if p.strip()]
        # валидируем email'ы
        for e in parts:
            try:
                validate_email(e)
            except ValidationError:
                raise ValidationError(f'Неправильный email: {e}')
        # убираем дубликаты, сохраняя порядок
        seen = set()
        uniq = []
        for e in parts:
            if e not in seen:
                seen.add(e)
                uniq.append(e)
        return uniq

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < datetime.date.today():
            raise ValidationError('Дедлайн не может быть в прошлом.')
        return deadline
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