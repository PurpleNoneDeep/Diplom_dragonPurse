from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, logout
from django.db.models import Sum
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from .forms import SharedAccountForm, RegisterForm, TransactionForm, CategoryForm
from .models import Notification, Category, Transaction
from django.contrib.auth.models import User
from django.utils import timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from .models import Transaction, Category
import datetime
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from .forms import GoalForm
from .models import Goal, UserGoal
from django.shortcuts import get_object_or_404
User = get_user_model()

@login_required
def goal_detail(request, goal_id):
    """
    Подробная страница цели:
    - информация о цели
    - участники и их доли
    - транзакции, связанные с этой целью
    """
    goal = get_object_or_404(Goal, id=goal_id)
    user = request.user

    # Проверяем, что пользователь участвует в цели
    if not UserGoal.objects.filter(goal=goal, user=user).exists():
        messages.error(request, "Вы не участвуете в этой цели.")
        return redirect('yourapp:goals_list')

    # Все участники
    participants = UserGoal.objects.filter(goal=goal).select_related('user')

    # Транзакции по этой цели
    transactions = Transaction.objects.filter(goal=goal).select_related('user', 'category')

    # Общая сумма накопленного (всеми участниками)
    total_saved = sum(t.amount for t in transactions)

    # Общая цель
    total_goal_amount = sum(u.amount for u in participants)

    # Процент выполнения
    percent = (total_saved / total_goal_amount * 100) if total_goal_amount > 0 else 0

    context = {
        'goal': goal,
        'participants': participants,
        'transactions': transactions,
        'total_saved': total_saved,
        'total_goal_amount': total_goal_amount,
        'percent': round(percent, 2),
    }

    return render(request, 'yourapp/goal_detail.html', context)



@login_required
def goals_list(request):
    user = request.user
    user_goals = UserGoal.objects.filter(user=user).select_related('goal')

    goals_data = []
    for user_goal in user_goals:
        goal = user_goal.goal

        # Сумма транзакций, связанных с этой целью
        total_saved = (
            Transaction.objects.filter(user=user, goal=goal)
            .aggregate(total=Sum('amount'))['total'] or 0
        )

        # Процент накопления
        percent = 0
        if user_goal.amount > 0:
            percent = (total_saved / user_goal.amount) * 100

        # Статус цели: если процент 100 — автоматически completed
        if percent >= 100 and goal.status != 'completed':
            goal.status = 'completed'
            goal.save()
        if percent < 33:
            color = '#f44336'
        elif percent < 66:
            color = '#ff9800'
        else:
            color = '#4caf50'
        # внутри цикла for user_goal in user_goals:
        goals_data.append({
            'id': goal.id,  # <--- добавляем
            'name': goal.name,
            'description': goal.description,
            'deadline': goal.deadline,
            'amount': user_goal.amount,
            'status': goal.get_status_display(),
            'percent': round(percent, 2),
            'saved': total_saved,
            'color': color,
        })

    context = {'goals_data': goals_data}
    return render(request, 'accounts/goals_list.html', context)

@login_required
def add_goal(request):
    """
    Создаёт Goal и соответствующие UserGoal — сумма распределяется поровну
    между участниками. Если пользователя с email не существует, создаём
    временного (is_active=False) пользователя с unusable password.
    """
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                goal = form.save()  # сохраняем Goal (name, description, deadline, status)
                total_amount = form.cleaned_data['amount']  # Decimal
                emails = list(form.cleaned_data['participants'])  # список email

                # добавить текущего пользователя, если у него есть email и он не в списке
                if request.user.email and request.user.email not in emails:
                    emails.append(request.user.email)

                # если совсем нет участников — наименее странное поведение: назначаем текущего пользователя
                if not emails:
                    emails = [request.user.email]

                # Получаем/создаём пользователей
                participants = []
                for email in emails:
                    # username: локальная часть + случайная строка, чтобы избежать конфликтов
                    defaults = {
                        'username': email.split('@')[0] + get_random_string(6),
                        'is_active': False,
                    }
                    user, created = User.objects.get_or_create(email=email, defaults=defaults)
                    if created:
                        # делаем пароль недоступным (пользователь не может залогиниться)
                        user.set_unusable_password()
                        user.save()
                    participants.append(user)

                # распределяем сумму поровну с учётом округления до 2 знаков:
                num = len(participants)
                share = (total_amount / Decimal(num)).quantize(Decimal('0.01'))
                total_assigned = share * num
                remainder = total_amount - total_assigned  # может быть 0.01/0.02 и т.д.

                for i, user in enumerate(participants):
                    user_amount = share
                    # добавляем остаток к первому участнику (можно изменить логику)
                    if i == 0 and remainder != Decimal('0.00'):
                        user_amount += remainder
                    UserGoal.objects.create(user=user, goal=goal, amount=user_amount)

            messages.success(request, 'Цель успешно создана.')
            # перенаправь на нужную страницу: список целей или детали
            return redirect('goals_list')  # замени на реальный URL name
    else:
        form = GoalForm()

    return render(request, 'accounts/add_goal.html', {'form': form})

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
        user = request.user

        # Сумма всех доходов
        income_total = (
                Transaction.objects.filter(
                    user=user,
                    category__category_type='income'
                ).aggregate(total=Sum('amount'))['total'] or 0
        )

        # Сумма всех расходов
        expense_total = (
                Transaction.objects.filter(
                    user=user,
                    category__category_type='expense'
                ).aggregate(total=Sum('amount'))['total'] or 0
        )

        # Баланс = доходы - расходы
        balance = income_total - expense_total

        context = {
            'balance': balance,
            'income_total': income_total,
            'expense_total': expense_total,
        }
        return render(request, 'accounts/dashboard.html', context)
