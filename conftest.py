import pytest


@pytest.fixture(autouse=True)
def senha_rapida_nos_testes(settings):
    """Troca o hash de senha por um rápido, só nos testes.

    O hasher padrão é lento de propósito (dificulta quebrar senha vazada).
    Nos testes isso só atrasa: cada create_user custava uns 300 ms.
    """
    settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
