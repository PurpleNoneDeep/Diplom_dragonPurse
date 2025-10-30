from django.contrib import admin
from .models import Notification, Category, Transaction
from django.contrib import admin
from .models import Settings, Analytics, Dragon, Wishlist, PlannedExpense, Goal, UserGoal

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'value')
    search_fields = ('user__username', 'key')

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'income_sum', 'expense_sum', 'balance')
    search_fields = ('user__username',)

@admin.register(Dragon)
class DragonAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood')
    search_fields = ('user__username',)

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'status')
    search_fields = ('user__username', 'name')

@admin.register(PlannedExpense)
class PlannedExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'status', 'date', 'repeat')
    search_fields = ('user__username', 'name')

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'deadline')
    search_fields = ('name',)

@admin.register(UserGoal)
class UserGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal', 'amount')
    search_fields = ('user__username', 'goal__name')
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'is_read')  # Поля, которые будут отображаться в списке
    list_filter = ('is_read', 'user')  # Фильтры по полям
    search_fields = ('message',)  # Поля для поиска

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'category_type')  # Поля, которые будут отображаться в списке
    list_filter = ('category_type', 'user')  # Фильтры по полям
    search_fields = ('name',)  # Поля для поиска

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'category', 'description')  # Поля, которые будут отображаться в списке
    list_filter = ('date', 'user', 'category')  # Фильтры по полям
    search_fields = ('description',)  # Поля для поиска