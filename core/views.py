# core/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings

# 使用装饰器确保只有登录用户才能访问此页面
@login_required
def index(request):
    # 将配置的交易对传递给模板
    context = {
        'tracked_pairs': [pair.upper() for pair in settings.TRACKED_PAIRS]
    }
    return render(request, 'index.html', context)
