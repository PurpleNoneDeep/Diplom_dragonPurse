from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, logout
from django.db.models import Sum
from django.db.models.functions import ExtractYear, ExtractMonth
from django.views import View
import json
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
from django.utils.dateparse import parse_date
from .models import Transaction, Category, Analytics
from django.views.decorators.http import require_POST

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

    # Получаем текущие настройки
    current_color = Settings.objects.filter(user=request.user, key='theme_color').first()
    current_color_value = current_color.value if current_color else ''

    return render(request, 'accounts/settings.html', {'form': form, 'current_color': current_color_value})

def index(request):
    user = request.user
    return render(request, "accounts/index.html", context={'user': request.user})

@login_required
@require_POST
def save_report(request):
    user = request.user

    start_date = parse_date(request.POST.get("start_date"))
    end_date = parse_date(request.POST.get("end_date"))
    selected_category = request.POST.get("category")
    selected_type = request.POST.get("type")

    # снова собираем queryset
    transactions = Transaction.objects.filter(user=user)

    if start_date:
        transactions = transactions.filter(date__date__gte=start_date)
    if end_date:
        transactions = transactions.filter(date__date__lte=end_date)
    if selected_category:
        transactions = transactions.filter(category__id=selected_category)
    if selected_type:
        transactions = transactions.filter(category__category_type=selected_type)

    # вычисляем суммы
    income_sum = transactions.filter(category__category_type="income").aggregate(total=models.Sum("amount"))["total"] or 0
    expense_sum = transactions.filter(category__category_type="expense").aggregate(total=models.Sum("amount"))["total"] or 0
    balance = income_sum - expense_sum

    # создаём запись Analytics
    Analytics.objects.create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        income_sum=income_sum,
        expense_sum=expense_sum,
        balance=balance
    )

    return redirect("report_builder")


@login_required
def report_builder(request):
    user = request.user

    # Базовый queryset — только транзакции пользователя
    transactions = Transaction.objects.filter(user=user).order_by('-date')
    categories = Category.objects.filter(user=user)
    filtered = False  # Флаг, чтобы показать кнопку "Сохранить"
    start_date = end_date = selected_category = selected_type = None

    if request.method == "POST" and "compose_report" in request.POST:

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
            return render(request, "accounts/report.html", {
                "error": "Нет доступных данных для построения графика.",
                "categories": categories,
                "filtered": filtered,
                "start_date": start_date,
                "end_date": end_date,
                "selected_category": selected_category,
                "selected_type": selected_type,
                "transactions": transactions,
            })

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

        return render(request, "accounts/report.html", context)

    # Сохраняем промежуточные значения в контекст
    context = {
        "transactions": transactions,
        "categories": categories,
        "filtered": filtered,
        "start_date": start_date,
        "end_date": end_date,
        "selected_category": selected_category,
        "selected_type": selected_type,
    }

    return render(request, "accounts/report.html", context)



@login_required
def notifications_inbox(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, "accounts/notifications.html", {"notifications": notifications})




@login_required
def notifications_all(request):
    notifications = Notification.objects.all()
    return render(request, "accounts/notifications.html", {"notifications": notifications})


@login_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    return render(request, "accounts/notification_detail.html", {"notification": notification})


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.is_read = True
    notification.save()
    return redirect("notifications_inbox")


@login_required
def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if request.method == "POST":
        notification.delete()
    return redirect("notifications_inbox")


@login_required
def shared_users_list(request):
    """Список пользователей, открывших доступ текущему"""
    accesses = SharedAccess.objects.filter(shared_with=request.user)
    return render(request, 'accounts/shared_users.html', {'accesses': accesses})


@login_required
def friend_goals(request, user_id):
    """Просмотр целей друга"""
    shared_access = get_object_or_404(
        SharedAccess,
        owner_id=user_id,
        shared_with=request.user,
        can_view_goals=True
    )
    goals = Goal.objects.filter(user_goals__user=shared_access.owner).distinct()
    return render(request, 'accounts/friend_goals.html', {
        'friend': shared_access.owner,
        'goals': goals
    })


@login_required
def friend_wishlist(request, user_id):
    """Просмотр вишлиста друга"""
    shared_access = get_object_or_404(
        SharedAccess,
        owner_id=user_id,
        shared_with=request.user,
        can_view_wishlist=True
    )
    wishlist = Wishlist.objects.filter(user=shared_access.owner)
    return render(request, 'accounts/friend_wishlist.html', {
        'friend': shared_access.owner,
        'wishlist': wishlist
    })



@login_required
def shared_account_view(request):
    if request.method == 'POST':
        form = SharedAccessInviteForm(request.POST)
        if form.is_valid():
            receiver = form.cleaned_data['receiver_email']
            message_text = form.cleaned_data['message']

            # Проверим, не было ли уже приглашения
            existing = SharedAccessInvite.objects.filter(
                sender=request.user,
                receiver=receiver,
                status='pending'
            ).exists()
            if existing:
                messages.warning(request, "Приглашение этому пользователю уже отправлено и ожидает ответа.")
            else:
                SharedAccessInvite.objects.create(
                    sender=request.user,
                    receiver=receiver,
                    message=message_text
                )
                Notification.objects.create(
                    user=receiver,
                    message=f"🔔 {request.user.username} пригласил(а) вас к совместному доступу к данным."
                )
                messages.success(request, "Приглашение успешно отправлено!")
            return redirect('shared_account')
    else:
        form = SharedAccessInviteForm()

    return render(request, 'accounts/shared_account.html', {'form': form})


@login_required
def invites_list(request):
    invites = SharedAccessInvite.objects.filter(receiver=request.user).order_by('-created_at')
    return render(request, 'accounts/invites_list.html', {'invites': invites})


@login_required
def handle_invite(request, invite_id, action):
    invite = get_object_or_404(SharedAccessInvite, id=invite_id, receiver=request.user)

    if action == 'accept':
        invite.status = 'accepted'
        SharedAccess.objects.get_or_create(
            owner=invite.sender,
            shared_with=invite.receiver
        )
        Notification.objects.create(
            user=invite.sender,
            message=f"✅ {invite.receiver.username} принял(а) приглашение к совместному доступу!"
        )
        messages.success(request, f"Вы приняли приглашение от {invite.sender.username}.")
    elif action == 'decline':
        invite.status = 'declined'
        Notification.objects.create(
            user=invite.sender,
            message=f"❌ {invite.receiver.username} отклонил(а) приглашение к совместному доступу."
        )
        messages.info(request, f"Вы отклонили приглашение от {invite.sender.username}.")
    invite.save()
    return redirect('invites_list')




@login_required
def planned_expense_list(request):
    # Проверяем напоминания для текущего пользователя
    today = timezone.localdate()
    now_time = timezone.localtime().time()

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
                    message=f"🔔 Напоминание: сегодня запланирована транзакция '{expense.name}'!"
                )

    return render(request, 'accounts/planned_expense_list.html', {'planned_items': planned_items})


@login_required
def planned_expense_create(request):
    if request.method == 'POST':
        form = PlannedExpenseForm(request.POST)
        if form.is_valid():
            planned = form.save(commit=False)
            planned.user = request.user
            planned.save()
            messages.success(request, "Планируемая транзакция успешно добавлена!")
            return redirect('planned_expense_list')
    else:
        form = PlannedExpenseForm()
    return render(request, 'accounts/planned_expense_form.html', {'form': form, 'title': 'Добавить запланированную транзакцию'})


@login_required
def planned_expense_edit(request, pk):
    planned = get_object_or_404(PlannedExpense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PlannedExpenseForm(request.POST, instance=planned)
        if form.is_valid():
            form.save()
            messages.success(request, "Планируемая транзакция обновлена!")
            return redirect('planned_expense_list')
    else:
        form = PlannedExpenseForm(instance=planned)
    return render(request, 'accounts/planned_expense_form.html', {'form': form, 'title': 'Редактировать транзакцию'})


@login_required
def planned_expense_delete(request, pk):
    planned = get_object_or_404(PlannedExpense, pk=pk, user=request.user)
    if request.method == 'POST':
        planned.delete()
        messages.success(request, "Планируемая транзакция удалена.")
        return redirect('planned_expense_list')
    return render(request, 'accounts/planned_expense_confirm_delete.html', {'planned': planned})



@login_required
def wishlist_create(request):
    if request.method == 'POST':
        form = WishlistForm(request.POST)
        if form.is_valid():
            wishlist = form.save(commit=False)
            wishlist.user = request.user
            wishlist.save()
            return redirect('wishlist_list')
    else:
        form = WishlistForm()
    return render(request, 'accounts/wishlist_form.html', {'form': form, 'title': 'Добавить желание'})

@login_required
def wishlist_edit(request, pk):
    wishlist = get_object_or_404(Wishlist, pk=pk, user=request.user)
    if request.method == 'POST':
        form = WishlistForm(request.POST, instance=wishlist)
        if form.is_valid():
            form.save()
            return redirect('wishlist_list')
    else:
        form = WishlistForm(instance=wishlist)
    return render(request, 'accounts/wishlist_form.html', {'form': form, 'title': 'Редактировать желание'})

@login_required
def wishlist_delete(request, pk):
    wishlist = get_object_or_404(Wishlist, pk=pk, user=request.user)
    if request.method == 'POST':
        wishlist.delete()
        return redirect('wishlist_list')
    return render(request, 'accounts/wishlist_confirm_delete.html', {'wishlist': wishlist})


@login_required
def goal_delete(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, f"Цель «{goal.name}» успешно удалена!")
        return redirect('goals_list')
    return redirect('goal_detail', goal_id=goal.id)


@login_required
def goal_detail(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)

    # Все участники этой цели
    participants = UserGoal.objects.filter(goal=goal).select_related('user')

    # Общие суммы
    total_goal_amount = sum((p.amount for p in participants), Decimal('0'))
    total_saved = sum((p.saved for p in participants), Decimal('0'))

    # Рассчёт общего процента выполнения
    percent = 0
    if total_goal_amount > 0:
        percent = (total_saved / total_goal_amount * 100).quantize(Decimal('0.01'))

    # Все транзакции, относящиеся к этой цели
    transactions = Transaction.objects.filter(goal=goal).select_related('user', 'category').order_by('-date')

    return render(request, 'accounts/goal_detail.html', {
        'goal': goal,
        'participants': participants,
        'transactions': transactions,
        'total_goal_amount': total_goal_amount,
        'total_saved': total_saved,
        'percent': percent,
    })




@login_required
def goals_list(request):
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

    return render(request, 'accounts/goals_list.html', {'goals': goals_data})


@login_required
def add_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                goal = form.save()

                total_amount = form.cleaned_data['amount']
                emails = list(form.cleaned_data['participants'])
                if request.user.email and request.user.email not in emails:
                    emails.append(request.user.email)

                if not emails:
                    emails = [request.user.email]

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

            messages.success(request, 'Цель успешно создана.')
            return redirect('goals_list')  # обязательно с namespace
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

        if len(dates) == 0 or len(amounts) == 0:
            return render(request, 'accounts/analytics.html', {'error': 'Нет доступных данных для построения графика.'})

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
            category.user = request.user
            category.save()
            return redirect('category_list')
        return render(request, 'accounts/category_form.html', {'form': form})

class TransactionDeleteView(View):
    def post(self, request, pk):
        transaction = get_object_or_404(Transaction, id=pk, user=request.user)
        transaction.delete()
        return redirect('transaction_list')


def transaction_list(request):
    # Получаем параметры
    selected_year = request.GET.get('year')
    selected_month = request.GET.get('month')
    selected_day = request.GET.get('day')

    transactions = Transaction.objects.filter(user=request.user).select_related('category')

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
        current_date = timezone.now().date()

        return render(request, 'accounts/transaction_form.html', {
            'categories_income': categories_income,
            'categories_expense': categories_expense,
            'goals': goals,
            'form': TransactionForm(),
            'current_date': current_date,
        })

    def post(self, request):
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
                return redirect('transaction_list')
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
            return redirect('transaction_list')

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

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
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
        now = timezone.now()

        # Определение первого и последнего дня текущего месяца
        first_day_of_month = now.replace(day=1)
        last_day_of_month = (first_day_of_month + timezone.timedelta(days=31)).replace(day=1) - timezone.timedelta(
            days=1)

        # Сумма всех доходов за текущий месяц
        income_total = (
                Transaction.objects.filter(
                    user=user,
                    category__category_type='income',
                    date__gte=first_day_of_month,
                    date__lte=last_day_of_month
                ).aggregate(total=Sum('amount'))['total'] or 0
        )

        # Сумма всех расходов за текущий месяц
        expense_total = (
                Transaction.objects.filter(
                    user=user,
                    category__category_type='expense',
                    date__gte=first_day_of_month,
                    date__lte=last_day_of_month
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


@login_required
def wishlist_list(request):
    shared_users = SharedAccess.objects.filter(shared_with=request.user).values_list('owner', flat=True)
    wishlists = Wishlist.objects.filter(models.Q(user=request.user) | models.Q(user__in=shared_users))
    return render(request, 'accounts/wishlist_list.html', {'wishlists': wishlists})