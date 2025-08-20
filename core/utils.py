# core/utils.py
from django.conf import settings
from cryptography.fernet import Fernet

# 关键：确保你的 settings.py 中有一个强大的、随机生成的SECRET_KEY
# 并且额外生成一个专门用于数据加密的密钥
# 在 settings.py 中添加:
# FERNET_KEY = Fernet.generate_key()
# 千万不要将FERNET_KEY硬编码在代码中或提交到git仓库
# 你可以使用环境变量来管理它
try:
    key = settings.FERNET_KEY
    cipher_suite = Fernet(key)
except AttributeError:
    raise RuntimeError("settings.py 中缺少 FERNET_KEY 配置")


def encrypt(text: str) -> str:
    """Encrypts a string."""
    if not text:
        return ""
    encoded_text = text.encode('utf-8')
    encrypted_text = cipher_suite.encrypt(encoded_text)
    return encrypted_text.decode('utf-8')


def decrypt(encrypted_text: str) -> str:
    """Decrypts a string."""
    if not encrypted_text:
        return ""
    try:
        encrypted_text_bytes = encrypted_text.encode('utf-8')
        decrypted_text = cipher_suite.decrypt(encrypted_text_bytes)
        return decrypted_text.decode('utf-8')
    except Exception:
        # 如果解密失败（例如密钥错误或数据损坏），返回空字符串
        return ""