# core/forms.py
from django import forms
from .models import APIKey

class APIKeyForm(forms.ModelForm):
    # 我们需要明文输入，所以覆盖模型中的字段
    api_key = forms.CharField(widget=forms.PasswordInput(render_value=True), label="API Key")
    secret_key = forms.CharField(widget=forms.PasswordInput(render_value=True), label="Secret Key")

    class Meta:
        model = APIKey
        fields = [
            'exchange', 'api_key', 'secret_key',
            'is_active', 'trade_amount_usdt',
            'buy_spread_percentage', 'sell_spread_percentage'
        ]