"""Regras da receita enviada por autor, num lugar só.

Usadas pelo formulário do painel (authors.forms.RecipeForm) e pela API
(api.serializers.MyRecipeSerializer). Se as regras ficassem copiadas nos
dois, uma porta acabaria aceitando o que a outra recusa.

As funções levantam a ValidationError do Django, que tanto o formulário
quanto o serializer do DRF sabem transformar em mensagem de erro.
"""
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

TIME_UNITS = [('minutos', 'minutos'), ('horas', 'horas')]
SERVINGS_UNITS = [
    ('porções', 'porções'),
    ('fatias', 'fatias'),
    ('unidades', 'unidades'),
    ('pessoas', 'pessoas'),
]
MIN_TITLE_LENGTH = 5
MAX_COVER_SIZE = 2 * 1024 * 1024

REQUIRED_MESSAGE = 'Este campo é obrigatório.'


def clean_title(title):
    title = title.strip()
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError(
            f'O título precisa ter pelo menos {MIN_TITLE_LENGTH} caracteres.',
        )
    return title


def clean_positive(value):
    if value <= 0:
        raise ValidationError('Informe um número maior que zero.')
    return value


def clean_cover(cover):
    # Na edição sem foto nova, cover é o arquivo que já está salvo; só a
    # foto enviada agora precisa passar pelo limite.
    is_new_upload = isinstance(cover, UploadedFile)
    if is_new_upload and cover.size > MAX_COVER_SIZE:
        raise ValidationError('A imagem pode ter no máximo 2 MB.')
    return cover


def check_description(title, description):
    """Erro (só a mensagem) se a descrição repete o título, ou None."""
    if title and title.strip().lower() == (description or '').strip().lower():
        return 'A descrição não pode ser igual ao título.'
    return None
