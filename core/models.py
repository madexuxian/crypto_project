from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from .utils import encrypt, decrypt  # 我们稍后会创建这个文件


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # 可以在这里添加更多用户相关的设置

    def __str__(self):
        return self.user.username


class APIKey(models.Model):
    EXCHANGE_CHOICES = [
        ('binance', 'Binance'),
        ('okx', 'OKX'),
        ('htx', 'HTX'),
    ]

    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES)

    # 我们将加密后的密钥以文本形式存储
    encrypted_api_key = models.TextField()
    encrypted_secret_key = models.TextField()

    # 交易机器人配置
    is_active = models.BooleanField(default=False, help_text="是否激活此API Key进行交易")
    trade_amount_usdt = models.DecimalField(max_digits=10, decimal_places=2, default=10.0,
                                            help_text="单次交易的USDT数量")
    buy_spread_percentage = models.DecimalField(max_digits=5, decimal_places=4,
                                                help_text="触发买入的价差百分比, e.g., 0.003 for 0.3%")
    sell_spread_percentage = models.DecimalField(max_digits=5, decimal_places=4,
                                                 help_text="触发卖出的价差百分比范围, e.g., 0.0003 for 0.03%")

    # 状态管理
    has_open_position = models.BooleanField(default=False, help_text="是否持有通过此策略买入的仓位")

    def set_keys(self, api_key, secret_key):
        self.encrypted_api_key = encrypt(api_key)
        self.encrypted_secret_key = encrypt(secret_key)

    def get_api_key(self):
        return decrypt(self.encrypted_api_key)

    def get_secret_key(self):
        return decrypt(self.encrypted_secret_key)

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.get_exchange_display()}"

    class Meta:
        # 每个用户在每个交易所只能有一对key
        unique_together = ('user_profile', 'exchange')