from django.urls import path
from .views import LoginView, LogoutView, DashboardView, RegisterView, ProfileView, SettingsView, SharedAccountView, \
    TransactionCreateView, TransactionListView, CategoryCreateView, CategoryListView, \
    TransactionDeleteView, AnalyticsView, ReportView, add_goal, goals_list, goal_detail, goal_delete, wishlist_list, \
    wishlist_create, wishlist_edit, wishlist_delete, planned_expense_list, planned_expense_create, planned_expense_edit, \
    planned_expense_delete, notifications_list, shared_account_view, invites_list, handle_invite

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('shared-account/', SharedAccountView.as_view(), name='shared_account'),
    path('notifications/', notifications_list, name='notifications_list'),
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/new/', TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/delete/<int:pk>/', TransactionDeleteView.as_view(), name='transaction_delete'),
    path('categories/new/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('report/', ReportView.as_view(), name='report'),
    path('goals/add/', add_goal, name='add_goal'),
    path('goals/', goals_list, name='goals_list'),
    path('goals/<int:goal_id>/', goal_detail, name='goal_detail'),
    path('<int:goal_id>/delete/', goal_delete, name='goal_delete'),
    path('wishlist/', wishlist_list, name='wishlist_list'),
    path('wishlist/add/', wishlist_create, name='wishlist_create'),
    path('wishlist/<int:pk>/edit/', wishlist_edit, name='wishlist_edit'),
    path('wishlist/<int:pk>/delete/', wishlist_delete, name='wishlist_delete'),
    path('planned/', planned_expense_list, name='planned_expense_list'),
    path('planned/add/', planned_expense_create, name='planned_expense_create'),
    path('planned/<int:pk>/edit/', planned_expense_edit, name='planned_expense_edit'),
    path('planned/<int:pk>/delete/', planned_expense_delete, name='planned_expense_delete'),
    path('shared/', shared_account_view, name='shared_account'),
    path('invites/', invites_list, name='invites_list'),
    path('invites/<int:invite_id>/<str:action>/', handle_invite, name='handle_invite'),
]