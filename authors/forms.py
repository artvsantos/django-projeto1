from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class RegisterForm(forms.ModelForm):
    """Cadastro de autor.

    A senha passa pelos mesmos validadores do AUTH_PASSWORD_VALIDATORS, com
    os dados digitados no formulário, para barrar senha parecida com o nome
    de usuário mesmo antes de o User existir no banco.
    """

    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'placeholder': 'Crie uma senha'}),
        help_text=(
            'Pelo menos 8 caracteres. Não pode ser só números, nem parecida '
            'com seu nome ou e-mail.'
        ),
    )
    password2 = forms.CharField(
        label='Confirme a senha',
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Digite a senha de novo'},
        ),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'username': 'Nome de usuário',
            'email': 'E-mail',
        }
        help_texts = {
            'username': 'Letras, números e @ . + - _ apenas.',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Ex.: Maria'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Ex.: Souza'}),
            'username': forms.TextInput(
                attrs={'placeholder': 'Ex.: mariasouza'},
            ),
            'email': forms.EmailInput(
                attrs={'placeholder': 'Ex.: maria@email.com'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No User do Django esses campos são opcionais; aqui não.
        for name in ('first_name', 'last_name', 'email'):
            self.fields[name].required = True

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Já existe uma conta com este e-mail.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password and password2 and password != password2:
            self.add_error('password2', 'As senhas não conferem.')

        if password:
            user = User(
                username=cleaned_data.get('username', ''),
                first_name=cleaned_data.get('first_name', ''),
                last_name=cleaned_data.get('last_name', ''),
                email=cleaned_data.get('email', ''),
            )
            try:
                validate_password(password, user=user)
            except ValidationError as error:
                self.add_error('password', error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Nome de usuário',
        widget=forms.TextInput(attrs={'placeholder': 'Seu nome de usuário'}),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'placeholder': 'Sua senha'}),
    )
