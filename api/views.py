import math

from django.db.models import Count, Q
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from api.serializers import (
    CategorySerializer, MyRecipeSerializer, RecipeDetailSerializer,
    RecipeListSerializer,
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


class MyRecipeViewSet(viewsets.ModelViewSet):
    """Suas receitas, publicadas ou não. Exige token.

    Mesmas regras do painel: receita nova ou editada fica fora do ar até
    o admin aprovar, e receita de outro autor dá 404.
    """

    serializer_class = MyRecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_view_name(self):
        return 'Minha receita' if self.detail else 'Minhas receitas'

    def get_queryset(self):
        # Filtrar pelo autor faz a receita de outra pessoa dar 404, sem
        # nem revelar que aquele id existe.
        return Recipe.objects.filter(
            author=self.request.user,
        ).select_related('category').order_by('-id')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, is_published=False)

    def perform_update(self, serializer):
        # Editar não pode virar atalho para mudar receita já aprovada.
        serializer.save(is_published=False)


class TokenView(ObtainAuthToken):
    """POST com username e password devolve o token. DELETE apaga o token.

    Use o token no cabeçalho: Authorization: Token <seu token>
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAuthenticated()]
        return super().get_permissions()

    def delete(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def throttled(self, request, wait):
        # A tradução do DRF ("Pedido foi suprimido") não explica nada.
        seconds = math.ceil(wait)
        unit = 'segundo' if seconds == 1 else 'segundos'
        exc = Throttled(
            detail=f'Muitas tentativas. Tente de novo em {seconds} {unit}.',
        )
        exc.wait = wait  # mantém o cabeçalho Retry-After
        raise exc
