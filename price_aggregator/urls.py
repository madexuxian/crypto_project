# price_aggregator/urls.py

from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- 请重点检查这一行 ---
    # 确保 path 函数的第一个参数是空字符串 ''
    path('', core_views.index, name='index'),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]