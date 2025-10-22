from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SharedAccountForm, RegisterForm, TransactionForm, CategoryForm
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification, Category, Transaction
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

class CategoryListView(View):
    def get(self, request):
        categories = Category.objects.filter(user=request.user)  # Получаем категории текущего пользователя
        return render(request, 'accounts/category_list.html', {'categories': categories})

class CategoryCreateView(View):
    def get(self, request):
        form = CategoryForm()
        return render(request, 'accounts/category_form.html', {'form': form})

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user  # Привязываем категорию к текущему пользователю
            category.save()
            return redirect('category_list')  # Перенаправление на страницу списка категорий
        return render(request, 'accounts/category_form.html', {'form': form})

class TransactionListView(View):
    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user).order_by('-date')  # Получаем транзакции текущего пользователя
        return render(request, 'accounts/transaction_list.html', {'transactions': transactions})

class TransactionCreateView(View):
    def get(self, request):
        form = TransactionForm()
        categories = Category.objects.filter(user=request.user)  # Получаем категории текущего пользователя
        return render(request, 'accounts/transaction_form.html', {'form': form, 'categories': categories})

    def post(self, request):
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user  # Привязываем транзакцию к текущему пользователю
            transaction.save()
            return redirect('transaction_list')  # Перенаправление на список транзакций
        categories = Category.objects.filter(user=request.user)
        return render(request, 'accounts/transaction_form.html', {'form': form, 'categories': categories})

class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        return render(request, 'accounts/notifications.html', {'notifications': notifications})


class SharedAccountView(View):
    def get(self, request):
        form = SharedAccountForm()
        return render(request, 'accounts/shared_account.html', {'form': form})

    def post(self, request):
        form = SharedAccountForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            access_data = form.cleaned_data['access_data']

            # Найдите пользователя по введенному email
            try:
                recipient_user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'Пользователь с таким адресом электронной почты не найден.')
                return render(request, 'accounts/shared_account.html', {'form': form})

            # Создание уведомления для указанного пользователя
            message = f'Вам предоставлен доступ к: {", ".join(access_data)}.'
            notification = Notification(user=recipient_user, message=message)
            notification.save()

            messages.success(request, 'Уведомление отправлено!')
            return redirect('shared_account')
        else:
            messages.error(request, 'Ошибка в форме. Пожалуйста, исправьте и повторите попытку.')
            return render(request, 'accounts/shared_account.html', {'form': form})


class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/settings.html')

class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        # Здесь можно добавить данные, которые нужно передать в шаблон
        return render(request, 'accounts/profile.html', {'user': request.user})

class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Храните пароль в зашифрованном виде
            user.save()
            login(request, user)  # Вход после регистрации
            return redirect('dashboard')
        return render(request, 'accounts/register.html', {'form': form})

class LoginView(View):
    def get(self, request):
        return render(request, 'accounts/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Неверные учетные данные.')
            return render(request, 'accounts/login.html')
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/dashboard.html')
