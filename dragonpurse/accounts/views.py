from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import SharedAccountForm, RegisterForm, TransactionForm, CategoryForm
from .models import Notification, Category, Transaction
from django.contrib.auth.models import User
from django.utils import timezone
import matplotlib
matplotlib.use('Agg')  # Установка неинтерактивного бэкенда перед импортом pyplot
import matplotlib.pyplot as plt
import io
import base64
from django.http import HttpResponse
from django.shortcuts import render
from .models import Transaction, Category
import datetime
from decimal import Decimal


class AnalyticsView(View):
    def get(self, request):
        categories = Category.objects.all()

        # Фильтры
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        category_id = request.GET.get('category')

        # Применение фильтров
        transactions = Transaction.objects.all()
        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)
        if category_id:
            transactions = transactions.filter(category_id=category_id)

        dates = []
        amounts = []

        for transaction in transactions:

            if isinstance(transaction.date, datetime.date):

                dates.append(transaction.date)
            if isinstance(transaction.amount, (int, Decimal)):
                amounts.append(float(transaction.amount))


        # Проверка на совпадение размеров
        if len(dates) == 0 or len(amounts) == 0:
            return render(request, 'accounts/analytics.html', {'error': 'Нет доступных данных для построения графика.'})

        # Убедитесь, что длины совпадают
        if len(dates) != len(amounts):
            return render(request, 'accounts/analytics.html', {'error': 'Данные о транзакциях неполные.'})

        # Создание графика
        plt.figure()
        plt.plot(dates, amounts, marker='o')
        plt.title('Транзакции')
        plt.xlabel('Дата')
        plt.ylabel('Сумма')
        plt.xticks(rotation=90)

        # Сохранение графика в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        return render(request, 'accounts/analytics.html',
                      {'plot_url': image_base64, 'categories': categories, 'start_date': start_date,
                       'end_date': end_date, 'category_id': category_id, 'transactions': transactions})

class ReportView(View):
    def get(self, request):

        transactions = Transaction.objects.filter(user=request.user)
        return render(request, 'accounts/report.html', {'transactions': transactions})

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

class TransactionDeleteView(View):
    def post(self, request, pk):
        transaction = get_object_or_404(Transaction, id=pk, user=request.user)
        transaction.delete()
        return redirect('transaction_list')

class TransactionListView(View):
    def get(self, request):
        today = timezone.now()
        date_filter = request.GET.get('date', today.date())

        transactions = Transaction.objects.filter(
            user=request.user,
            date__date=date_filter
        ).order_by('-date')

        return render(request, 'accounts/transaction_list.html', {
            'transactions': transactions,
            'selected_date': date_filter,
            'today': today.date(),
        })

class TransactionCreateView(View):
    def get(self, request):
        categories_income = list(
            Category.objects.filter(category_type='income', user=request.user).values('id', 'name'))
        categories_expense = list(
            Category.objects.filter(category_type='expense', user=request.user).values('id', 'name'))
        current_date = timezone.now().date()
        return render(request, 'accounts/transaction_form.html', {
            'categories_income': categories_income,
            'categories_expense': categories_expense,
            'form': TransactionForm(),
            'current_date': current_date,
        })

    def post(self, request):
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        # Получаем дату из формы, если не выбрана, используем текущую
        date_str = request.POST.get('newdate')
        if date_str:  # Проверяем, если дата была выбрана
            date_num = timezone.datetime.strptime(date_str, '%Y-%m-%d')  # Преобразуем строку в объект даты
            print(date_num)
        else:
            date_num = timezone.now()  # Используем текущую дату, если дата не выбрана

        transaction = Transaction(
            user=request.user,
            category_id=category_id,
            description=description,
            amount=amount,
            date=date_num  # Устанавливаем выбранную дату
        )
        transaction.save()
        return redirect('transaction_list')

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

