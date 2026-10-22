from django.contrib.auth.models import User
from django.test import TestCase
from parameterized import parameterized

from authors.forms import RegisterForm


class AuthorRegisterFormTest(TestCase):
    def setUp(self) -> None:
        self.form_data = {
            'first_name': 'Maria',
            'last_name': 'Souza',
            'username': 'mariasouza',
            'email': 'maria@email.com',
            'password': 'Tempero#Forte2026',
            'password2': 'Tempero#Forte2026',
        }
        return super().setUp()

    def test_form_is_valid_with_correct_data(self):
        form = RegisterForm(data=self.form_data)
        self.assertTrue(form.is_valid(), form.errors)

    @parameterized.expand([
        'first_name',
        'last_name',
        'username',
        'email',
        'password',
        'password2',
    ])
    def test_field_is_required(self, field):
        self.form_data[field] = ''
        form = RegisterForm(data=self.form_data)

        self.assertFalse(form.is_valid())
        self.assertIn('Este campo é obrigatório.', form.errors[field])

    def test_passwords_must_match(self):
        self.form_data['password2'] = 'Outra#Senha2026'
        form = RegisterForm(data=self.form_data)

        self.assertFalse(form.is_valid())
        self.assertIn('As senhas não conferem.', form.errors['password2'])

    @parameterized.expand([
        ('curta', 'Ab#1'),
        ('so_numeros', '73920184756'),
        ('comum', 'password123'),
    ])
    def test_weak_password_is_rejected(self, _name, password):
        self.form_data['password'] = password
        self.form_data['password2'] = password
        form = RegisterForm(data=self.form_data)

        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_password_too_similar_to_username_is_rejected(self):
        self.form_data['username'] = 'tempero2026'
        self.form_data['password'] = 'tempero2026'
        self.form_data['password2'] = 'tempero2026'
        form = RegisterForm(data=self.form_data)

        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_email_must_be_unique_ignoring_case(self):
        User.objects.create_user(
            username='outra', email='maria@email.com', password='x',
        )
        self.form_data['email'] = 'MARIA@Email.com'
        form = RegisterForm(data=self.form_data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Já existe uma conta com este e-mail.', form.errors['email']
        )

    def test_username_must_be_unique(self):
        User.objects.create_user(username='mariasouza', password='x')
        form = RegisterForm(data=self.form_data)

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_save_stores_hashed_password(self):
        form = RegisterForm(data=self.form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertNotEqual(user.password, self.form_data['password'])
        self.assertTrue(user.check_password(self.form_data['password']))

    def test_labels_are_in_portuguese(self):
        form = RegisterForm()
        labels = {name: field.label for name, field in form.fields.items()}

        self.assertEqual(labels, {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'username': 'Nome de usuário',
            'email': 'E-mail',
            'password': 'Senha',
            'password2': 'Confirme a senha',
        })
