"""Dados que todo template precisa, sem passar view por view."""
from recipes.models import Category


def menu_categories(request):
    """Categorias que tem ao menos uma receita publicada.

    Vai para o menu do cabecalho. Categoria sem receita ficaria como um
    link para uma pagina 404, entao nao entra.
    """
    return {
        'menu_categories': Category.objects.filter(
            recipe__is_published=True
        ).distinct().order_by('name')
    }
