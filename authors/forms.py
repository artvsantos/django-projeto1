from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from recipes.models import Recipe


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


class RecipeForm(forms.ModelForm):
    """Receita enviada pelo autor no painel.

    is_published e preparation_steps_is_html ficam de fora de propósito:
    quem publica é o admin, e HTML vindo do usuário abriria espaço para
    injetar script na página da receita.
    """

    TIME_UNITS = [('minutos', 'minutos'), ('horas', 'horas')]
    SERVINGS_UNITS = [
        ('porções', 'porções'),
        ('fatias', 'fatias'),
        ('unidades', 'unidades'),
        ('pessoas', 'pessoas'),
    ]
    MAX_COVER_SIZE = 2 * 1024 * 1024
    # O form é em duas colunas; esses ocupam a linha inteira.
    full_width_fields = ('description', 'preparation_steps', 'cover')

    preparation_time_unit = forms.ChoiceField(
        label='Unidade', choices=TIME_UNITS,
    )
    servings_unit = forms.ChoiceField(label='Unidade', choices=SERVINGS_UNITS)

    class Meta:
        model = Recipe
        fields = [
            'title', 'category', 'description',
            'preparation_time', 'preparation_time_unit',
            'servings', 'servings_unit',
            'preparation_steps', 'cover',
        ]
        labels = {
            'title': 'Título',
            'description': 'Descrição',
            'category': 'Categoria',
            'preparation_time': 'Tempo de preparo',
            'servings': 'Rendimento',
            'preparation_steps': 'Modo de preparo',
            'cover': 'Foto da receita',
        }
        help_texts = {
            'description': 'Uma frase curta que aparece na lista de receitas.',
            'cover': 'JPG ou PNG, até 2 MB. Opcional.',
        }
        widgets = {
            'title': forms.TextInput(
                attrs={'placeholder': 'Ex.: Bolo de cenoura'},
            ),
            'description': forms.TextInput(
                attrs={'placeholder': 'Ex.: Fofinho, com calda de chocolate'},
            ),
            'preparation_steps': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Um passo por linha.',
            }),
            'cover': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = True
        self.fields['category'].empty_label = 'Escolha uma categoria'

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 5:
            raise ValidationError(
                'O título precisa ter pelo menos 5 caracteres.',
            )
        return title

    def _positive(self, field):
        value = self.cleaned_data[field]
        if value <= 0:
            raise ValidationError('Informe um número maior que zero.')
        return value

    def clean_preparation_time(self):
        return self._positive('preparation_time')

    def clean_servings(self):
        return self._positive('servings')

    def clean_cover(self):
        cover = self.cleaned_data.get('cover')
        # Na edição sem foto nova, cover é o arquivo que já está salvo;
        # só a foto enviada agora precisa passar pelo limite.
        is_new_upload = isinstance(cover, UploadedFile)
        if is_new_upload and cover.size > self.MAX_COVER_SIZE:
            raise ValidationError('A imagem pode ter no máximo 2 MB.')
        return cover

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title', '')
        description = cleaned_data.get('description', '')

        if title and title.lower() == description.strip().lower():
            self.add_error(
                'description', 'A descrição não pode ser igual ao título.',
            )
        return cleaned_data
