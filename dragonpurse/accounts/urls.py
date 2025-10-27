from django.urls import path
from .views import LoginView, LogoutView, DashboardView, RegisterView, ProfileView, SettingsView, SharedAccountView, \
    NotificationListView, TransactionCreateView, TransactionListView, CategoryCreateView, CategoryListView, \
    TransactionDeleteView, AnalyticsView, ReportView

urlpatterns = [
    path('', LoginView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('shared-account/', SharedAccountView.as_view(), name='shared_account'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/new/', TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/delete/<int:pk>/', TransactionDeleteView.as_view(), name='transaction_delete'),
    path('categories/new/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('report/', ReportView.as_view(), name='report'),
]