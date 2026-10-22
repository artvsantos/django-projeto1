from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse
from parameterized import parameterized

from authors import views
from authors.forms import LoginForm


class AuthorLoginFormTest(TestCase):
    @parameterized.expand(['username', 'password'])
    def test_field_is_required(self, field):
        data = {'username': 'mariasouza', 'password': 'Tempero#Forte2026'}
        data[field] = ''
        form = LoginForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('Este campo é obrigatório.', form.errors[field])

    def test_labels_are_in_portuguese(self):
        form = LoginForm()
        labels = {name: field.label for name, field in form.fields.items()}

        self.assertEqual(labels, {
            'username': 'Nome de usuário',
            'password': 'Senha',
        })


class AuthorLoginViewTest(TestCase):
    def setUp(self) -> None:
        self.url = reverse('authors:login')
        self.password = 'Tempero#Forte2026'
        self.user = User.objects.create_user(
            username='mariasouza',
            first_name='Maria',
            password=self.password,
        )
        return super().setUp()

    def login(self, password=None, next_url=None):
        url = self.url
        if next_url is not None:
            url = f'{url}?next={next_url}'
        return self.client.post(url, data={
            'username': 'mariasouza',
            'password': password or self.password,
        })

    def assertLoggedIn(self):
        self.assertEqual(
            self.client.session.get('_auth_user_id'), str(self.user.pk),
        )

    def assertNotLoggedIn(self):
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_url_is_correct(self):
        self.assertEqual(self.url, '/authors/login/')

    def test_login_uses_correct_view_function(self):
        self.assertIs(resolve(self.url).func, views.login_view)

    def test_login_get_loads_correct_template(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authors/pages/login.html')

    def test_login_with_valid_credentials_logs_user_in(self):
        response = self.login()

        self.assertLoggedIn()
        self.assertRedirects(response, reverse('recipes:home'))

    def test_login_shows_welcome_message(self):
        response = self.client.post(self.url, data={
            'username': 'mariasouza', 'password': self.password,
        }, follow=True)

        self.assertContains(response, 'Você entrou como Maria.')

    def test_login_with_wrong_password_shows_error(self):
        response = self.login(password='senha-errada')

        self.assertNotLoggedIn()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuário ou senha inválidos.')
        self.assertContains(response, 'value="mariasouza"')

    def test_login_never_sends_password_back_to_page(self):
        response = self.login(password='senha-errada')

        self.assertNotContains(response, 'senha-errada')

    def test_inactive_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()
        response = self.login()

        self.assertNotLoggedIn()
        self.assertContains(response, 'Usuário ou senha inválidos.')

    def test_login_redirects_to_next_when_it_is_a_local_url(self):
        response = self.login(next_url='/recipes/search/?q=bolo')

        self.assertRedirects(
            response, '/recipes/search/?q=bolo', fetch_redirect_response=False,
        )

    def test_failed_login_keeps_next_in_form_action(self):
        response = self.login(password='senha-errada', next_url='/recipes/1/')

        self.assertContains(
            response, 'action="/authors/login/?next=%2Frecipes%2F1%2F"',
        )

    def test_login_ignores_next_pointing_to_another_site(self):
        response = self.login(next_url='https://site-malicioso.com/')

        self.assertRedirects(response, reverse('recipes:home'))

    def test_login_page_links_to_register(self):
        response = self.client.get(self.url)

        self.assertContains(response, reverse('authors:register'))


class AuthorLogoutViewTest(TestCase):
    def setUp(self) -> None:
        self.url = reverse('authors:logout')
        self.user = User.objects.create_user(
            username='mariasouza', password='Tempero#Forte2026',
        )
        self.client.force_login(self.user)
        return super().setUp()

    def test_logout_url_is_correct(self):
        self.assertEqual(self.url, '/authors/logout/')

    def test_logout_with_get_is_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_with_post_logs_user_out(self):
        response = self.client.post(self.url)

        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(response, reverse('authors:login'))

    def test_logout_shows_message(self):
        response = self.client.post(self.url, follow=True)

        self.assertContains(response, 'Você saiu da sua conta.')


class HeaderAccountLinksTest(TestCase):
    def test_anonymous_user_sees_login_and_register_links(self):
        response = self.client.get(reverse('recipes:home'))

        self.assertContains(response, 'Entrar')
        self.assertContains(response, 'Criar conta')
        self.assertNotContains(response, reverse('authors:logout'))

    def test_logged_in_user_sees_name_and_logout_button(self):
        user = User.objects.create_user(
            username='mariasouza', first_name='Maria', password='x',
        )
        self.client.force_login(user)
        response = self.client.get(reverse('recipes:home'))

        self.assertContains(response, 'Olá, Maria')
        self.assertContains(response, reverse('authors:logout'))
