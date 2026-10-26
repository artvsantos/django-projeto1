from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class TokenApiTest(APITestCase):
    url = '/api/v1/token/'

    def setUp(self) -> None:
        # O limite de tentativas guarda a contagem no cache; sem limpar,
        # um teste herdaria as tentativas do anterior.
        cache.clear()
        self.user = User.objects.create_user(
            username='mariasouza', password='Tempero#Forte2026',
        )
        return super().setUp()

    def login(self, password='Tempero#Forte2026'):
        return self.client.post(self.url, {
            'username': 'mariasouza', 'password': password,
        })

    def test_url_is_correct(self):
        self.assertEqual(reverse('api:token'), self.url)

    def test_valid_credentials_return_a_token(self):
        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, {'token': Token.objects.get(user=self.user).key},
        )

    def test_logging_in_again_returns_the_same_token(self):
        first = self.login().data['token']
        second = self.login().data['token']

        self.assertEqual(first, second)

    def test_wrong_password_returns_400_without_token(self):
        response = self.login(password='senha-errada')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        self.assertFalse(Token.objects.exists())

    def test_inactive_user_cannot_get_a_token(self):
        self.user.is_active = False
        self.user.save()

        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_too_many_attempts_are_blocked(self):
        # Sem limite, dá para testar milhares de senhas por minuto.
        for _ in range(5):
            self.login(password='senha-errada')

        response = self.login()

        self.assertEqual(
            response.status_code, status.HTTP_429_TOO_MANY_REQUESTS,
        )
        # A tradução do DRF ("Pedido foi suprimido") não explica nada.
        self.assertRegex(
            str(response.data['detail']),
            r'^Muitas tentativas\. Tente de novo em \d+ segundos?\.$',
        )

    def test_delete_revokes_the_token(self):
        token = self.login().data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.delete(self.url)
        after = self.client.get('/api/v1/my-recipes/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=token).exists())
        self.assertEqual(after.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_without_token_returns_401(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
