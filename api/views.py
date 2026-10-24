from django.db.models import Count, Q
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError

from api.serializers import (
    CategorySerializer, RecipeDetailSerializer, RecipeListSerializer,
)
from recipes.models import Category, Recipe


class RecipeViewSet(viewsets.ReadOnlyModelViewSet):
    """Receitas publicadas, das mais novas para as mais antigas.

    Filtros da lista: ?search=bolo procura no título e na descrição, e
    ?category=1 mostra só as receitas da categoria de id 1.
    """

    # O texto aparece na página da API no navegador; sem isso viria o nome
    # da classe em inglês ("Recipe List").
    def get_view_name(self):
        return 'Receita' if self.detail else 'Receitas'

    def get_queryset(self):
        recipes = Recipe.objects.filter(
            is_published=True,
        ).select_related('category', 'author').order_by('-id')

        params = self.request.query_params

        search = params.get('search', '').strip()
        if search:
            recipes = recipes.filter(
                Q(title__icontains=search) | Q(description__icontains=search),
            )

        category = params.get('category', '').strip()
        if category:
            if not category.isdigit():
                raise ValidationError(
                    {'category': 'Informe o id numérico da categoria.'},
                )
            recipes = recipes.filter(category_id=int(category))

        return recipes

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RecipeDetailSerializer
        return RecipeListSerializer


class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Categorias com pelo menos uma receita publicada."""

    serializer_class = CategorySerializer
    # São poucas; paginar só atrapalharia quem monta um menu com elas.
    pagination_class = None

    def get_view_name(self):
        return 'Categorias'

    def get_queryset(self):
        return Category.objects.annotate(
            recipes_count=Count('recipe', filter=Q(recipe__is_published=True)),
        ).filter(recipes_count__gt=0).order_by('name')
