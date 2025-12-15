from django.urls import path
from .views import IndexView, DashboardView, LoginView, LogoutView, TransactionListView, TransactionCreateView, \
    TransactionEditView, TransactionDeleteView, CategoryCreateView, CategoryListView, CategoryDeleteView, AddGoalView, \
    GoalDetailView, GoalsListView, GoalDeleteView, RegisterView, WishlistListView, WishlistCreateView, \
    WishlistDeleteView, WishlistEditView, ReportBuilderView, build_transactions_chart, DownloadChartView, \
    PlannedExpenseListView, PlannedExpenseCreateView, PlannedExpenseDeleteView, PlannedExpenseEditView, \
    NotificationMarkReadView, NotificationDeleteView, SharedAccountView, settings_view, \
    ProfileView, ChangeNameView, ChangeEmailView, ChangePasswordView, NotificationDetailView, SharedGoalsView, \
    SharedWishlistView, SettingsView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/new/', TransactionCreateView.as_view(), name='transaction_create'),
    path('transaction/edit/<int:transaction_id>/', TransactionEditView.as_view(), name='transaction_edit'),
    path('transaction/delete/<int:transaction_id>/', TransactionDeleteView.as_view(), name='transaction_delete'),
    path('categories/new/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('category/delete/<int:category_id>/', CategoryDeleteView.as_view(), name='category_delete'),
    path('goals/', GoalsListView.as_view(), name='goals_list'),
    path('goals/add/', AddGoalView.as_view(), name='add_goal'),
    path('goals/<int:goal_id>/', GoalDetailView.as_view(), name='goal_detail'),
    path('goals/delete/<int:goal_id>/', GoalDeleteView.as_view(), name='goal_delete'),
    path('wishlist/', WishlistListView.as_view(), name='wishlist_list'),
    path('wishlist/add/', WishlistCreateView.as_view(), name='wishlist_create'),
    path('wishlist/<int:pk>/delete/', WishlistDeleteView.as_view(), name='wishlist_delete'),
    path('wishlist/edit/<int:wishlist_id>/', WishlistEditView.as_view(), name='wishlist_edit'),
    path("report/", ReportBuilderView.as_view(), name="report_builder"),
    path("reports/download-chart/", DownloadChartView.as_view(), name="download_chart"),
    path('planned/', PlannedExpenseListView.as_view(), name='planned_expense_list'),
    path('planned/add/', PlannedExpenseCreateView.as_view(), name='planned_expense_create'),
    path('planned/<int:pk>/delete/', PlannedExpenseDeleteView.as_view(), name='planned_expense_delete'),
    path('planned/edit/<int:planned_id>/', PlannedExpenseEditView.as_view(), name='planned_edit'),
    path('notifications/', NotificationMarkReadView.as_view(), name='notifications_inbox'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification_detail'),
    path('notifications/<int:pk>/delete/', NotificationDeleteView.as_view(), name='notification_delete'),
    path('shared-account/', SharedAccountView.as_view(), name='shared_account'),
    path('shared-goals/', SharedGoalsView.as_view(), name='shared_goals'),
    path('shared-wishlist/', SharedWishlistView.as_view(), name='shared_wishlist'),
    path('settings/', settings_view, name='settings'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path("profile/change-name/", ChangeNameView.as_view(), name="change_name"),
    path("profile/change-email/", ChangeEmailView.as_view(), name="change_email"),
    path("profile/change-password/", ChangePasswordView.as_view(), name="change_password"),
    path('settings/interface', SettingsView.as_view(), name='settings_interface'),

]