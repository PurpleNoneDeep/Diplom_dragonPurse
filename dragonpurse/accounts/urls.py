from django.urls import path
from .views import LoginView, LogoutView, DashboardView, RegisterView, ProfileView, SettingsView, SharedAccountView, \
    TransactionCreateView, transaction_list, CategoryCreateView, CategoryListView, \
    TransactionDeleteView, AnalyticsView, ReportView, add_goal, goals_list, goal_detail, goal_delete, wishlist_list, \
    wishlist_create, wishlist_edit, wishlist_delete, planned_expense_list, planned_expense_create, planned_expense_edit, \
    planned_expense_delete, notifications_list, shared_account_view, invites_list, handle_invite, friend_wishlist, \
    shared_users_list, friend_goals, notification_delete, notification_mark_read, notification_detail, \
    notifications_all, notifications_inbox, report_builder, save_report, index, settings_view

urlpatterns = [
    path('', index, name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('settings/', settings_view, name='settings'),
    path('shared-account/', SharedAccountView.as_view(), name='shared_account'),
    path('notifications/', notifications_inbox, name='notifications_inbox'),
    path('notifications/all/', notifications_all, name='notifications_all'),
    path('notifications/<int:pk>/', notification_detail, name='notification_detail'),
    path('notifications/<int:pk>/read/', notification_mark_read, name='notification_mark_read'),
    path('notifications/<int:pk>/delete/', notification_delete, name='notification_delete'),
    path('transactions/', transaction_list, name='transaction_list'),
    path('transactions/new/', TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/delete/<int:pk>/', TransactionDeleteView.as_view(), name='transaction_delete'),
    path('categories/new/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path("report/", report_builder, name="report_builder"),
    path("report/save/", save_report, name="save_report"),
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
    path('shared/list/', shared_users_list, name='shared_users_list'),
    path('shared/<int:user_id>/goals/', friend_goals, name='friend_goals'),
    path('shared/<int:user_id>/wishlist/', friend_wishlist, name='friend_wishlist'),
    path('invites/', invites_list, name='invites_list'),
    path('invites/<int:invite_id>/<str:action>/', handle_invite, name='handle_invite'),
]