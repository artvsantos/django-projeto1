from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse

from authors import views


class AuthorRegisterViewTest(TestCase):
    def setUp(self) -> None:
        self.url = reverse('authors:register')
        self.form_data = {
            'first_name': 'Maria',
            'last_name': 'Souza',
            'username': 'mariasouza',
            'email': 'maria@email.com',
            'password': 'Tempero#Forte2026',
            'password2': 'Tempero#Forte2026',
        }
        return super().setUp()

    def test_register_url_is_correct(self):
        self.assertEqual(self.url, '/authors/register/')

    def test_register_uses_correct_view_function(self):
        self.assertIs(resolve(self.url).func, views.register)

    def test_register_get_loads_correct_template(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authors/pages/register.html')
        self.assertContains(response, 'Criar conta')

    def test_register_post_with_valid_data_creates_user(self):
        response = self.client.post(self.url, data=self.form_data)
        user = User.objects.get(username='mariasouza')

        self.assertRedirects(response, reverse('authors:login'))
        self.assertEqual(user.email, 'maria@email.com')
        self.assertTrue(user.check_password('Tempero#Forte2026'))

    def test_register_post_with_valid_data_shows_success_message(self):
        response = self.client.post(
            self.url, data=self.form_data, follow=True,
        )

        self.assertContains(response, 'Conta criada com sucesso')

    def test_register_post_with_invalid_data_keeps_typed_values(self):
        self.form_data['password2'] = 'Outra#Senha2026'
        response = self.client.post(self.url, data=self.form_data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertContains(response, 'As senhas não conferem.')
        self.assertContains(response, 'value="mariasouza"')

    def test_register_post_never_sends_password_back_to_page(self):
        self.form_data['password2'] = 'Outra#Senha2026'
        response = self.client.post(self.url, data=self.form_data)

        self.assertNotContains(response, 'Tempero#Forte2026')
