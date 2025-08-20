# core/urls.py
from django.urls import path
from .views import index, manage_api_keys, SignUpView

urlpatterns = [
    path('', index, name='index'),
    path('keys/', manage_api_keys, name='manage_api_keys'),
    path('signup/', SignUpView.as_view(), name='signup'),
]