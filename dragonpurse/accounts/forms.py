from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Transaction, Category, PlannedExpense
import re
import datetime
from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Goal, Wishlist
from .models import SharedAccessInvite

class SharedAccessInviteForm(forms.ModelForm):
    receiver_email = forms.EmailField(label="Email получателя")

    class Meta:
        model = SharedAccessInvite
        fields = ['receiver_email', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Комментарий (необязательно)...'}),
        }

    def clean_receiver_email(self):
        email = self.cleaned_data['receiver_email']
        try:
            receiver = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Пользователь с таким email не найден.")
        return receiver

class PlannedExpenseForm(forms.ModelForm):
    class Meta:
        model = PlannedExpense
        fields = ['name', 'description', 'date', 'repeat', 'status', 'reminder', 'reminder_time']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название транзакции'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Описание'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'repeat': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'reminder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reminder_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

class WishlistForm(forms.ModelForm):
    class Meta:
        model = Wishlist
        fields = ['name', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название желания'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Описание'}),
            'status': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Статус (например: Хочу / В процессе / Куплено)'}),
        }

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
        fields = ['date', 'category', 'description', 'amount', 'goal', 'goal_amount']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['goal'].queryset = Goal.objects.filter(user_goals__user=user)
        self.fields['goal'].required = False
        self.fields['goal_amount'].required = False

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