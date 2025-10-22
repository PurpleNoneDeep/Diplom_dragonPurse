from django.contrib import admin
from .models import Notification, Category, Transaction

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