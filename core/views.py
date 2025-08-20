# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic

from .forms import APIKeyForm
from .models import APIKey, UserProfile


# 【新增】注册视图
class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


@login_required
def index(request):
    return render(request, 'index.html')


@login_required
def manage_api_keys(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = APIKeyForm(request.POST)
        if form.is_valid():
            exchange = form.cleaned_data['exchange']
            api_key_instance, created = APIKey.objects.get_or_create(
                user_profile=user_profile,
                exchange=exchange
            )
            api_key_instance.is_active = form.cleaned_data['is_active']
            api_key_instance.trade_amount_usdt = form.cleaned_data['trade_amount_usdt']
            api_key_instance.buy_spread_percentage = form.cleaned_data['buy_spread_percentage']
            api_key_instance.sell_spread_percentage = form.cleaned_data['sell_spread_percentage']
            api_key_instance.set_keys(
                form.cleaned_data['api_key'],
                form.cleaned_data['secret_key']
            )
            api_key_instance.save()
            return redirect('manage_api_keys')
    else:
        form = APIKeyForm()

    keys = APIKey.objects.filter(user_profile=user_profile)
    # 【修改】模板路径不再需要'core/'前缀
    return render(request, 'manage_api_keys.html', {'form': form, 'keys': keys})