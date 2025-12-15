from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Sum, QuerySet
from django.db.models.functions import ExtractYear, ExtractMonth
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import View
import json
import io
from django.template.loader import render_to_string, get_template
from xhtml2pdf import pisa
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import FormView, UpdateView
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .forms import SharedAccountForm, RegisterForm, TransactionForm, CategoryForm, ChangeNameForm, ChangeEmailForm
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

from .forms import WishlistForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PlannedExpense, Notification
from .forms import PlannedExpenseForm
from django.db import models

from .models import SharedAccessInvite, SharedAccess, Notification, Wishlist
from .forms import SharedAccessInviteForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import SharedAccess, Goal, Wishlist, UserGoal


from django.shortcuts import render, get_object_or_404, redirect
from .models import Notification
from django.contrib.auth.decorators import login_required

from .forms import SettingsForm
from .models import Settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date, parse_datetime
from .models import Transaction, Category, Analytics
from django.views.decorators.http import require_POST
User = get_user_model()


class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        print("HELOOOOOOOOOOOO")
        now = timezone.localtime()
        current_date = now.date()
        current_time = now.time().replace(second=0, microsecond=0)

        planned_expenses = PlannedExpense.objects.filter(
            user=request.user,
            date=current_date,
            reminder=True,
            reminder_time__isnull=False
        )

        for expense in planned_expenses:
            if expense.reminder and expense.date == current_date:
                # Проверяем, есть ли уже уведомление на сегодня
                exists = Notification.objects.filter(
                    user=request.user,
                    message__icontains=expense.name,
                    created_at__date=current_date
                ).exists()
                if not exists:
                    Notification.objects.create(
                        user=request.user,
                        message=f"Напоминание: запланирована транзакция '{expense.name}'!",
                        notification_type="planned",
                        created_at = current_date
                    )

        return render(
            request,
            "accounts/index.html",
            context={'user': request.user}
        )

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        now = timezone.now()

        first_day_of_month = now.replace(day=1)
        last_day_of_month = (first_day_of_month + timezone.timedelta(days=31)).replace(day=1) - timezone.timedelta(
            days=1)

        transactions = Transaction.objects.filter(
            user=user,
            date__gte=first_day_of_month,
            date__lte=last_day_of_month
        ).order_by('date')

        income_total = transactions.filter(category__category_type='income').aggregate(total=Sum('amount'))[
                           'total'] or Decimal(0)
        expense_total = transactions.filter(category__category_type='expense').aggregate(total=Sum('amount'))[
                            'total'] or Decimal(0)
        balance = income_total - expense_total

        all_days = [first_day_of_month + timezone.timedelta(days=i) for i in
                    range((last_day_of_month - first_day_of_month).days + 1)]
        income_amounts = [0] * len(all_days)
        expense_amounts = [0] * len(all_days)

        for transaction in transactions:
            if transaction.date is None:
                continue  # Пропустить, если дата не указана

            # Рассчитываем индекс
            index = (transaction.date - first_day_of_month).days

            # Проверяем, что индекс находится в пределах массива
            if 0 <= index < len(income_amounts):
                if transaction.category.category_type == 'income':
                    income_amounts[index] += float(transaction.amount) if isinstance(transaction.amount,
                                                                                     Decimal) else transaction.amount
                elif transaction.category.category_type == 'expense':
                    expense_amounts[index] += float(transaction.amount) if isinstance(transaction.amount,
                                                                                      Decimal) else transaction.amount
            else:
                # Обработка случая, когда индекс вне допустимого диапазона
                # Например: logging, специальная обработка, пропуск и т.д.
                continue  # Или log an issue

        bar_colors = []
        for i in range(len(all_days)):
            if income_amounts[i] > 0:
                bar_colors.append('#639372')  # Зеленый для доходов
            if expense_amounts[i] > 0:
                bar_colors.append('#DC143C')  # Красный для расходов

        plt.figure(figsize=(10, 6))

        plt.bar([day.strftime('%Y-%m-%d') for day in all_days], income_amounts, color='#639372', alpha=0.7,
                label='Доходы')
        plt.bar([day.strftime('%Y-%m-%d') for day in all_days],
                expense_amounts, color='#DC143C', alpha=0.7, label='Расходы', bottom=income_amounts)

        plt.gca().set_facecolor('#131212')
        plt.grid(False)  # Убираем сетку

        plt.title('')  # Убираем заголовок
        plt.xlabel('Дата', color='#639372')
        plt.ylabel('Сумма', color='#639372')

        plt.xticks(rotation=45, ha='right', color='#639372')
        plt.yticks(color='#639372')
        plt.legend()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#131212')
        plt.close()
        buf.seek(0)
        image_png = buf.getvalue()
        buf.close()
        graphic = base64.b64encode(image_png).decode('utf-8')

        context = {
            'balance': balance,
            'income_total': income_total,
            'expense_total': expense_total,
            'graphic': graphic,
        }
        return render(request, 'accounts/dashboard.html', context)

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

class TransactionListView(View):
    def get(self, request):
        # Получаем параметры
        selected_year = request.GET.get('year')
        selected_month = request.GET.get('month')
        selected_day = request.GET.get('day')
        transaction_type = request.GET.get('type')  # Получаем тип транзакции
        category_name = request.GET.get('category_name')  # Получаем название категории для поиска

        transactions: QuerySet[Transaction] = Transaction.objects.filter(user=request.user).select_related('category')

        # Фильтр по году и месяцу
        if selected_year and selected_month:
            transactions = transactions.annotate(
                year=ExtractYear('date'),
                month=ExtractMonth('date')
            ).filter(
                year=int(selected_year),
                month=int(selected_month)
            )

        # Если выбран конкретный день — фильтруем также по дню
        if selected_day:
            transactions = transactions.filter(date__day=int(selected_day))

        # Фильтр по типу транзакции
        if transaction_type:
            transactions = transactions.filter(category__category_type=transaction_type)

        # Фильтр по названию категории
        if category_name:
            transactions = transactions.filter(category__name__icontains=category_name)

        # JSON для отображения в календаре
        transactions_json = json.dumps([
            {
                'date': t.date.strftime('%Y-%m-%d'),
                'category': t.category.name if t.category else 'Без категории',
                'amount': float(t.amount),
                'transaction_type': t.category.category_type if t.category else 'unknown',
            }
            for t in transactions
        ])

        return render(request, 'accounts/transaction_list.html', {
            'transactions': transactions,
            'transactions_json': transactions_json,
            'selected_year': selected_year,
            'selected_month': selected_month,
            'selected_day': selected_day,
            'transaction_type': transaction_type,  # Передаем выбранный тип транзакции в шаблон
            'category_name': category_name,  # Передаем введенное название категории для поиска
        })

class TransactionCreateView(View):
    def get(self, request):
        categories_income = list(
            Category.objects.filter(category_type='income', user=request.user).values('id', 'name')
        )
        categories_expense = list(
            Category.objects.filter(category_type='expense', user=request.user).values('id', 'name')
        )
        goals = Goal.objects.filter(user_goals__user=request.user).distinct()
        user_goal = UserGoal.objects.filter(user=request.user)
        available_goals = [
            user_goal.goal for user_goal in user_goal
            if user_goal.saved < user_goal.amount
        ]
        current_date = timezone.now().date()

        return render(request, 'accounts/transaction_form.html', {
            'categories_income': categories_income,
            'categories_expense': categories_expense,
            'goals': available_goals,
            'form': TransactionForm(),
            'current_date': current_date,
        })

    def post(self, request):
        print(request.POST)
        category_id = request.POST.get('category')
        new_category_name = request.POST.get('new_category')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        goal_id = request.POST.get('goal')
        goal_amount = request.POST.get('goal_amount')
        date_str = request.POST.get('newdate')

        if date_str:
            date_num = timezone.datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_num = timezone.now()

        # Определение типа категории
        if category_id == 'new':
            category_type = request.POST.get('category_type')
            if category_type not in ['income', 'expense']:
                messages.error(request, 'Некорректный тип категории.')
                return redirect('transaction_create')
            category = Category.objects.create(
                user=request.user,
                name=new_category_name,
                category_type=category_type
            )
            category_id = category.id  # Используйте ID только что созданной категории

        # Далее сохраняем транзакцию
        amount_decimal = Decimal(amount)
        goal_amount_decimal = Decimal(goal_amount) if goal_amount else None

        if goal_amount_decimal is not None and (goal_amount_decimal <= 0 or goal_amount_decimal > amount_decimal):
            messages.error(request, 'Сумма для цели должна быть положительной и не превышать сумму дохода.')
            return redirect('transaction_create')

        transaction = Transaction(
            user=request.user,
            category_id=category_id,
            description=description,
            amount=amount_decimal,
            date=date_num,
            goal_id=goal_id if goal_id else None,
            goal_amount=goal_amount_decimal if goal_amount_decimal else None,
        )
        transaction.save()

        if transaction.category and transaction.category.category_type == 'income' and goal_id and goal_amount_decimal:
            user_goal = UserGoal.objects.filter(user=request.user, goal_id=goal_id).first()
            if user_goal:
                user_goal.saved += goal_amount_decimal
                user_goal.save()
            else:
                UserGoal.objects.create(
                    user=request.user,
                    goal_id=goal_id,
                    amount=Decimal('0.00'),
                    saved=goal_amount_decimal
                )

        messages.success(request, 'Транзакция успешно добавлена.')
        return redirect('transaction_list')

class TransactionEditView(View):
    def get(self, request, transaction_id):
        transaction = get_object_or_404(Transaction, id=transaction_id)
        form = TransactionForm(instance=transaction)

        return render(request, 'accounts/transaction_edit.html', {'form': form})

    def post(self, request, transaction_id):
        transaction = get_object_or_404(Transaction, id=transaction_id)
        form = TransactionForm(request.POST, instance=transaction)

        if form.is_valid():
            form.save()
            return redirect('transaction_list')  # Перенаправление на детальный просмотр

        return render(request, 'accounts/transaction_edit.html', {'form': form})

class TransactionDeleteView(View):
    def post(self, request, transaction_id):
        transaction = get_object_or_404(Transaction, id=transaction_id)
        transaction.delete()  # Удаляем транзакцию
        return redirect('transaction_list')

#Работа с категориями
class CategoryCreateView(View):
    def get(self, request):
        form = CategoryForm()
        return render(request, 'accounts/category_form.html', {'form': form})

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['name']
            if Category.objects.filter(name=category_name).exists():
                messages.error(request, "Категория с таким названием уже существует.")
            else:
                category = form.save(commit=False)
                category.user = request.user
                category.save()
                messages.success(request, "Категория успешно добавлена.")
                return redirect('category_list')

        return render(request, 'accounts/category_form.html', {'form': form})

class CategoryListView(View):
    def get(self, request):
        # Получение значения типа категории из GET-запроса
        category_type = request.GET.get('category_type')

        # Фильтрация категорий по типу, если задано
        if category_type:
            categories = Category.objects.filter(user=request.user, category_type=category_type)
        else:
            categories = Category.objects.filter(user=request.user)  # Получаем все категории текущего пользователя

        return render(request, 'accounts/category_list.html', {'categories': categories, 'category_type': category_type})

class CategoryDeleteView(View):
    def post(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)
        category.delete()  # Удаляем транзакцию
        return redirect('category_list')

#Работа с целями
class AddGoalView(LoginRequiredMixin, FormView):
    form_class = GoalForm
    template_name = 'accounts/add_goal.html'

    def form_valid(self, form):
        with transaction.atomic():

            goal = form.save()
            total_amount = form.cleaned_data['amount']
            emails = list(form.cleaned_data['participants'])
            if self.request.user.email and self.request.user.email not in emails:
                emails.append(self.request.user.email)

            if not emails:
                emails = [self.request.user.email]

            participants = []

            for email in emails:
                defaults = {
                    'username': email.split('@')[0] + get_random_string(6),
                    'is_active': False,
                }
                user, created = User.objects.get_or_create(email=email, defaults=defaults)
                if created:
                    user.set_unusable_password()
                    user.save()
                participants.append(user)

            for user in participants:
                UserGoal.objects.create(
                    user=user,
                    goal=goal,
                    amount=Decimal(total_amount)
                )

        messages.success(self.request, 'Цель успешно создана.')
        return redirect('goals_list')  # обязательно с namespace

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response({'form': form})


class GoalDetailView(LoginRequiredMixin, View):
    template_name = 'accounts/goal_detail.html'

    def get(self, request, goal_id):
        goal = get_object_or_404(Goal, id=goal_id)

        participants = UserGoal.objects.filter(goal=goal).select_related('user')
        total_goal_amount = sum((p.amount for p in participants), Decimal('0'))
        total_saved = sum((p.saved for p in participants), Decimal('0'))

        percent = 0
        if total_goal_amount > 0:
            percent = (total_saved / total_goal_amount * 100).quantize(Decimal('0.01'))

        # Проверка и обновление статуса
        if total_saved >= total_goal_amount:
            goal.status = 'completed'
            goal.save()

        transactions = Transaction.objects.filter(goal=goal).select_related('user', 'category').order_by('-date')

        return render(request, self.template_name, {
            'goal': goal,
            'participants': participants,
            'transactions': transactions,
            'total_goal_amount': total_goal_amount,
            'total_saved': total_saved,
            'percent': percent,
        })
class GoalsListView(LoginRequiredMixin, View):
    template_name = 'accounts/goals_list.html'

    def get(self, request):
        user_goals = UserGoal.objects.filter(user=request.user).select_related('goal')
        goals_data = []

        for ug in user_goals:
            goal = ug.goal
            total_saved = (UserGoal.objects.filter(goal=goal)
                           .aggregate(total=Sum('amount'))['total'] or 0)
            percent = min(100, (ug.saved / ug.amount * 100) if ug.amount > 0 else 0)

            if percent < 33:
                color = '#f44336'
            elif percent < 66:
                color = '#ff9800'
            else:
                color = '#4caf50'

            goals_data.append({
                'id': goal.id,
                'name': goal.name,
                'description': goal.description,
                'deadline': goal.deadline,
                'amount': ug.amount,
                'status': goal.get_status_display(),
                'percent': round(percent, 2),
                'saved': ug.saved,
                'color': color,
            })

        return render(request, self.template_name, {'goals': goals_data})
class GoalDeleteView(View):
    def post(self, request, goal_id):
        goal = get_object_or_404(Goal, id=goal_id)
        goal.delete()  # Удаляем транзакцию
        return redirect('goals_list')

#Список желаний
class WishlistListView(LoginRequiredMixin, View):
    template_name = 'accounts/wishlist.html'

    def get(self, request):
        # Получаем пользователей, с которыми списки желаемого были поделены
        shared_users = SharedAccess.objects.filter(shared_with=request.user).values_list('owner', flat=True)

        # Получаем списки желаемого для текущего пользователя и для пользователей, с которыми он разделил доступ
        wishlists = Wishlist.objects.filter(models.Q(user=request.user) | models.Q(user__in=shared_users))

        # Рендерим шаблон с полученными списками
        return render(request, self.template_name, {'wishlists': wishlists})

class WishlistCreateView(LoginRequiredMixin, FormView):
    form_class = WishlistForm
    template_name = 'accounts/wishlist_form.html'
    title = 'Добавить желание'

    def form_valid(self, form):
        wishlist = form.save(commit=False)
        wishlist.user = self.request.user
        wishlist.save()
        return redirect('wishlist_list')

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response({'form': form, 'title': self.title})

class WishlistDeleteView(LoginRequiredMixin, View):
    template_name = 'accounts/wishlist_confirm_delete.html'

    def get(self, request, pk):
        # Получаем объект списка желаемого, доступный только для текущего пользователя
        wishlist = get_object_or_404(Wishlist, pk=pk, user=request.user)
        return render(request, self.template_name, {'wishlist': wishlist})

    def post(self, request, pk):
        # Получаем объект списка желаемого и удаляем его
        wishlist = get_object_or_404(Wishlist, pk=pk, user=request.user)
        wishlist.delete()
        return redirect('wishlist_list')

class WishlistEditView(View):
    def get(self, request, wishlist_id):
        wishlist = get_object_or_404(Wishlist, id=wishlist_id)
        form = WishlistForm(instance=wishlist)

        return render(request, 'accounts/wishlist_edit.html', {'form': form})

    def post(self, request, wishlist_id):
        wishlist = get_object_or_404(Wishlist, id=wishlist_id)
        form = WishlistForm(request.POST, instance=wishlist)

        if form.is_valid():
            form.save()
            return redirect('wishlist_list')  # Перенаправление на детальный просмотр

        return render(request, 'accounts/wishlist_edit.html', {'form': form})

import base64

class ReportBuilderView(LoginRequiredMixin, View):
    template_name = "accounts/report.html"

    def get(self, request):
        user = request.user
        transactions = Transaction.objects.filter(user=user).order_by('-date')
        categories = Category.objects.filter(user=user)

        # Начальное состояние для отображения
        context = {
            "transactions": transactions,
            "categories": categories,
            "filtered": False,
            "start_date": None,
            "end_date": None,
            "selected_category": None,
            "selected_type": None,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user

        # Базовый queryset — только транзакции пользователя
        transactions = Transaction.objects.filter(user=user).order_by('-date')
        categories = Category.objects.filter(user=user)

        # 1. Получаем значения полей
        start_date = parse_date(request.POST.get("start_date"))
        end_date = parse_date(request.POST.get("end_date"))
        selected_category = request.POST.get("category")
        selected_type = request.POST.get("type")  # income / expense

        # 2. Фильтруем
        if start_date:
            transactions = transactions.filter(date__date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__date__lte=end_date)
        if selected_category:
            transactions = transactions.filter(category__id=selected_category)
        if selected_type:
            categories = categories.filter(category_type=selected_type)

        filtered = True

        # Подготовка данных для графика
        dates = []
        amounts = []
        for transaction in transactions:
            if isinstance(transaction.date, datetime.date):
                dates.append(transaction.date)
            if isinstance(transaction.amount, (int, Decimal)):
                amounts.append(float(transaction.amount))

        # Проверка наличия данных для графика
        if not dates or not amounts:
            context = {
                "error": "Нет доступных данных для построения графика.",
                "categories": categories,
                "filtered": filtered,
                "start_date": start_date,
                "end_date": end_date,
                "selected_category": selected_category,
                "selected_type": selected_type,
                "transactions": transactions,
            }
            return render(request, self.template_name, context)

        # Создание графика
        plt.figure(figsize=(10, 5))
        plt.style.use('dark_background')  # Устанавливаем темный фон

        # Разбиваем транзакции на доходы и расходы
        income_dates = []
        income_amounts = []
        expense_dates = []
        expense_amounts = []

        for transaction in transactions:
            if transaction.category.category_type == "income":  # Предположим, что положительные суммы — это доход
                income_dates.append(transaction.date)
                income_amounts.append(float(transaction.amount))
            if transaction.category.category_type == "expense":  # Предположим, что отрицательные суммы — это расходы
                expense_dates.append(transaction.date)
                expense_amounts.append(float(abs(transaction.amount)))  # Делаем их положительными для графика

        # График доходов
        if income_dates and income_amounts:
            plt.plot(income_dates, income_amounts, marker='o', color='#639372', label='Доходы')

        # График расходов
        if expense_dates and expense_amounts:
            plt.plot(expense_dates, expense_amounts, marker='o', color='red', label='Расходы')

        plt.title('Транзакции')
        plt.xlabel('Дата')
        plt.ylabel('Сумма')
        plt.xticks(rotation=90)

        # Настройка фона
        plt.gca().set_facecolor('#131212')
        plt.xticks(rotation=45, ha='right', color='#639372')
        plt.yticks(color='#639372')  # Устанавливаем фон графика

        # Добавляем легенду
        plt.legend()

        # Сохранение графика в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#131212')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        # Добавляем график и данные в контекст
        context = {
            "transactions": transactions,
            "categories": categories,
            "filtered": filtered,
            "start_date": start_date,
            "end_date": end_date,
            "selected_category": selected_category,
            "selected_type": selected_type,
            "plot_url": image_base64,  # График в формате base64
        }

        return render(request, self.template_name, context)



def build_transactions_chart(transactions):
    plt.figure(figsize=(10, 5))
    plt.style.use('dark_background')

    income_dates, income_amounts = [], []
    expense_dates, expense_amounts = [], []

    for t in transactions:
        if t.category.category_type == "income":
            income_dates.append(t.date)
            income_amounts.append(float(t.amount))
        elif t.category.category_type == "expense":
            expense_dates.append(t.date)
            expense_amounts.append(float(abs(t.amount)))

    if income_dates:
        plt.plot(
            income_dates,
            income_amounts,
            marker='o',
            color='#639372',
            label='Доходы'
        )

    if expense_dates:
        plt.plot(
            expense_dates,
            expense_amounts,
            marker='o',
            color='red',
            label='Расходы'
        )

    plt.title('Транзакции')
    plt.xlabel('Дата')
    plt.ylabel('Сумма')
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)

    return buf

class DownloadChartView(LoginRequiredMixin, View):

    def post(self, request):
        user = request.user

        transactions = Transaction.objects.filter(user=user).order_by('-date')

        start_date = parse_date(request.POST.get("start_date"))
        end_date = parse_date(request.POST.get("end_date"))
        selected_category = request.POST.get("category")
        selected_type = request.POST.get("type")

        if start_date:
            transactions = transactions.filter(date__date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__date__lte=end_date)
        if selected_category:
            transactions = transactions.filter(category__id=selected_category)
        if selected_type:
            transactions = transactions.filter(
                category__category_type=selected_type
            )

        buf = build_transactions_chart(transactions)

        response = HttpResponse(
            buf.getvalue(),
            content_type="image/png"
        )
        response["Content-Disposition"] = (
            'attachment; filename="transactions_chart.png"'
        )

        return response

#Запланированные транзакции
class PlannedExpenseListView(LoginRequiredMixin, View):
    template_name = 'accounts/planned_expense_list.html'

    def get(self, request):
        # Проверяем напоминания для текущего пользователя
        today = timezone.localdate()
        planned_items = PlannedExpense.objects.filter(user=request.user)

        for expense in planned_items:
            if expense.reminder and expense.date == today:
                # Проверяем, есть ли уже уведомление на сегодня
                exists = Notification.objects.filter(
                    user=request.user,
                    message__icontains=expense.name,
                    created_at__date=today
                ).exists()
                if not exists:
                    Notification.objects.create(
                        user=request.user,
                        message=f"Напоминание: сегодня запланирована транзакция '{expense.name}'!",
                        notification_type="planned",
                        created_at=expense.reminder_time
                    )

        return render(request, self.template_name, {'planned_items': planned_items})

class PlannedExpenseCreateView(LoginRequiredMixin, FormView):
    form_class = PlannedExpenseForm
    template_name = 'accounts/planned_expense_form.html'
    title = 'Добавить запланированную транзакцию'

    def form_valid(self, form):
        planned = form.save(commit=False)
        planned.user = self.request.user
        planned.save()
        messages.success(self.request, "Планируемая транзакция успешно добавлена!")
        return redirect('planned_expense_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

class PlannedExpenseDeleteView(LoginRequiredMixin, View):
    template_name = 'accounts/planned_expense_confirm_delete.html'

    def get(self, request, pk):
        planned = get_object_or_404(PlannedExpense, pk=pk, user=request.user)
        return render(request, self.template_name, {'planned': planned})

    def post(self, request, pk):
        planned = get_object_or_404(PlannedExpense, pk=pk, user=request.user)
        planned.delete()
        messages.success(request, "Планируемая транзакция удалена.")
        return redirect('planned_expense_list')

class PlannedExpenseEditView(View):
    def get(self, request, planned_id):
        planned = get_object_or_404(PlannedExpense, id=planned_id)
        form = PlannedExpenseForm(instance=planned)

        return render(request, 'accounts/planned_expense_edit.html', {'form': form})

    def post(self, request, planned_id):
        planned = get_object_or_404(PlannedExpense, id=planned_id)
        form = PlannedExpenseForm(request.POST, instance=planned)

        if form.is_valid():
            form.save()
            return redirect('planned_expense_list')  # Перенаправление на детальный просмотр

        return render(request, 'accounts/planned_expense_edit.html', {'form': form})

#Уведомления
class NotificationMarkReadView(LoginRequiredMixin, View):
    template_name = 'accounts/notifications.html'  # Укажите путь к вашему шаблону

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        return render(request, self.template_name, {'notifications': notifications})
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        notification.is_read = True
        notification.save()
        return redirect("notifications_inbox")


class NotificationDetailView(View):
    def get(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        invite = get_object_or_404(SharedAccessInvite)
        form = SharedAccountForm(initial={'email': invite.sender.email})
        return render(request, "accounts/notification_detail.html", {"notification": notification, "form":form, "invite":invite})

    def post(self, request, pk):
        action = request.POST.get('action')

        sender_email = request.POST.get('sender_email')

        invite = get_object_or_404(
            SharedAccessInvite,
            sender__email=sender_email,
            receiver=request.user
        )
        action = request.POST.get('action')

        # ---------- ОТКЛОНЕНИЕ ----------
        if action == 'decline':
            invite.status = 'declined'
            invite.save()

            messages.info(request, "Доступ отклонён.")
            return redirect('notifications_inbox')

        # ---------- ПРИНЯТИЕ ----------
        if action == 'accept':
            form = SharedAccountForm(request.POST)

            if not form.is_valid():
                notification = get_object_or_404(Notification, pk=pk)
                return render(
                    request,
                    "accounts/notification_detail.html",
                    {
                        "notification": notification,
                        "form": form
                    }
                )

            # ===== 1. ДАННЫЕ ОТ ПОЛЬЗОВАТЕЛЯ B =====
            access_data_b = form.cleaned_data['access_data']

            can_b_goals = 'goals' in access_data_b
            can_b_wishlist = 'wishlist' in access_data_b

            user_a = invite.sender     # тот, кто первым открыл доступ
            user_b = invite.receiver   # тот, кто сейчас нажал кнопку

            # ===== 2. ДАННЫЕ ОТ ПОЛЬЗОВАТЕЛЯ A =====
            access_data_a = []

            if invite.message:
                access_data_a = [
                    item.strip() for item in invite.message.split(',')
                ]

            can_a_goals = 'goals' in access_data_a
            can_a_wishlist = 'wishlist' in access_data_a

            # ===== 3. СОЗДАЁМ ДОСТУП A → B =====
            SharedAccess.objects.update_or_create(
                owner=user_a,
                shared_with=user_b,
                defaults={
                    'can_view_goals': can_a_goals,
                    'can_view_wishlist': can_a_wishlist
                }
            )

            # ===== 4. СОЗДАЁМ ДОСТУП B → A =====
            SharedAccess.objects.update_or_create(
                owner=user_b,
                shared_with=user_a,
                defaults={
                    'can_view_goals': can_b_goals,
                    'can_view_wishlist': can_b_wishlist
                }
            )

            # ===== 5. ОБНОВЛЯЕМ СТАТУС ПРИГЛАШЕНИЯ =====
            invite.status = 'accepted'
            invite.save()

            messages.success(request, "Взаимный доступ успешно настроен.")
            return redirect('notifications_inbox')


class NotificationDeleteView(LoginRequiredMixin, View):
    template_name = 'accounts/notification_confirm_delete.html'

    def get(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        return render(request, self.template_name, {'planned': notification})

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.delete()
        messages.success(request, "Планируемая транзакция удалена.")
        return redirect('notifications_inbox')


class SharedAccountView(View):
    def get(self, request):
        form = SharedAccountForm()

        # Все пользователи, которым ТЕКУЩИЙ пользователь дал доступ
        shared_with_users = SharedAccess.objects.filter(
            owner=request.user
        ).select_related('shared_with')
        received_accesses = SharedAccess.objects.filter(
            shared_with=request.user
        ).select_related('owner')
        return render(
            request,
            'accounts/shared_account.html',
            {
                'form': form,
                'shared_with_users': shared_with_users, "received_accesses":received_accesses
            }
        )


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
            message = f'Вам предоставлен доступ к: {", ".join(access_data)}.\n'
            notification_type = "shared_access"
            now = timezone.localtime()
            current_date = now.date()

            # Сохраните уведомление
            notification = Notification(user=recipient_user, message=message, notification_type=notification_type, created_at=current_date)
            notification.save()

            # Сохраните данные в SharedAccessInvite
            invInvite = SharedAccessInvite(
                sender=request.user,
                receiver=recipient_user,
                message=message,
                status='pending'
            )
            invInvite.save()

            messages.success(request, 'Уведомление отправлено и приглашение создано!')
            return redirect('shared_account')
        else:
            messages.error(request, 'Ошибка в форме. Пожалуйста, исправьте и повторите попытку.')
            return render(request, 'accounts/shared_account.html', {'form': form})

def settings_view(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            selected_color = form.cleaned_data['theme_color']
            # Сохраняем в БД
            Settings.objects.update_or_create(
                user=request.user,
                key='theme_color',
                defaults={'value': selected_color}
            )
            return redirect('settings')  # Перенаправление на ту же страницу или другую после сохранения
    else:
        form = SettingsForm()
        return render(request, 'accounts/settings.html', {'form': form})

class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        # Здесь можно добавить данные, которые нужно передать в шаблон
        return render(request, 'accounts/profile_settings.html', {'user': request.user})

class ChangeNameView(LoginRequiredMixin, UpdateView):
    form_class = ChangeNameForm
    template_name = "accounts/change_name.html"
    success_url = reverse_lazy("profile")

    def get_object(self):
        return self.request.user

class ChangeEmailView(LoginRequiredMixin, UpdateView):
    form_class = ChangeEmailForm
    template_name = "accounts/change_email.html"
    success_url = reverse_lazy("profile")

    def get_object(self):
        return self.request.user

class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("profile")

class SharedGoalsView(LoginRequiredMixin, View):
    def get(self, request):
        # 1. Все доступы к целям для текущего пользователя
        accesses = (
            SharedAccess.objects
            .filter(
                shared_with=request.user,
                can_view_goals=True
            )
            .select_related('owner')
        )

        # 2. Все user_id владельцев, которые дали доступ
        owners = [access.owner for access in accesses]

        # 3. Цели этих пользователей
        shared_goals = (
            UserGoal.objects
            .filter(user__in=owners)
            .select_related('user', 'goal')
        )

        return render(
            request,
            'accounts/shared_goals.html',
            {
                'shared_goals': shared_goals
            }
        )

class SharedWishlistView(LoginRequiredMixin, View):
    def get(self, request):
        # 1. Все пользователи, которые дали текущему пользователю доступ к вишлисту
        accesses = (
            SharedAccess.objects
            .filter(
                shared_with=request.user,
                can_view_wishlist=True
            )
            .select_related('owner')
        )

        # 2. Владельцы вишлистов
        owners = [access.owner for access in accesses]

        # 3. Желания этих пользователей
        shared_wishlists = (
            Wishlist.objects
            .filter(user__in=owners)
            .select_related('user')
        )

        return render(
            request,
            'accounts/shared_wishlist.html',
            {
                'shared_wishlists': shared_wishlists
            }
        )

