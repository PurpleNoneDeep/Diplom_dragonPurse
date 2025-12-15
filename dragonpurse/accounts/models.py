from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    CATEGORY_TYPES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Это поле должно быть здесь
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)

    def __str__(self):
        return self.name

class Goal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершено'),
    ]

    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True)
    deadline = models.DateField(verbose_name='Дедлайн')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')

    def __str__(self):
        return self.name

class UserGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_goals')
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='user_goals')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    saved = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Накоплено')

    def __str__(self):
        return f'{self.user.username} - {self.goal.name}'


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Цель')
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Сумма для цели')

    def __str__(self):
        return f"{self.date} - {self.category.name if self.category else 'Без категории'} - {self.amount}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(max_length=255, blank=True, null=True)  # Добавляем новое поле
    created_at = models.DateTimeField(auto_now_add=False)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message

class Settings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settings')
    key = models.CharField(max_length=255)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value} (User: {self.user.username})"


class Analytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    income_sum = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expense_sum = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Analytics for {self.user.username} from {self.start_date} to {self.end_date}"

class Dragon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dragons')
    mood = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Dragon of {self.user.username} - Mood: {self.mood}"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - Status: {self.status} (User: {self.user.username})"

class PlannedExpense(models.Model):
    REPEAT_CHOICES = [
        ('daily', 'Раз в день'),
        ('weekly', 'Раз в неделю'),
        ('monthly', 'Раз в месяц'),
        ('yearly', 'Раз в год'),
    ]

    STATUS_CHOICES = [
        ('in_progress', 'В работе'),
        ('completed', 'Выполнен'),
        ('deferred', 'Перенос'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='planned_expenses')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    date = models.DateField()
    repeat = models.CharField(max_length=10, choices=REPEAT_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, null=True, blank=True)
    reminder = models.BooleanField(default=False)
    reminder_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - Status: {self.status} (User: {self.user.username})"

class SharedAccess(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_accesses')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_accesses')
    can_view_goals = models.BooleanField(default=True)
    can_view_wishlist = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('owner', 'shared_with')

    def __str__(self):
        return f"{self.owner.username} → {self.shared_with.username}"


class SharedAccessInvite(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('accepted', 'Принято'),
        ('declined', 'Отклонено'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invites')
    message = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} ({self.status})"


#Просмотр целей друзей
