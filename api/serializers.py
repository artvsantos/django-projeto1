from rest_framework import serializers

from recipes import validation
from recipes.models import Category, Recipe


class CategorySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    # Vem do annotate na view: só conta receita publicada.
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'recipes_count']


class RecipeListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:recipe-detail')
    category = CategorySummarySerializer(read_only=True)
    author = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'url', 'title', 'slug', 'description', 'category',
            'author', 'preparation_time', 'preparation_time_unit',
            'servings', 'servings_unit', 'cover', 'created_at',
        ]

    def get_author(self, recipe):
        # Só o nome público. E-mail e o resto do User nunca saem da API.
        author = recipe.author
        if author is None:
            return None
        return author.get_full_name() or author.username

    def get_cover(self, recipe):
        if not recipe.cover:
            return None
        # No Cloudinary a URL já é absoluta; localmente vem "/media/...".
        return self.context['request'].build_absolute_uri(recipe.cover.url)


class RecipeDetailSerializer(RecipeListSerializer):
    class Meta(RecipeListSerializer.Meta):
        fields = RecipeListSerializer.Meta.fields + ['preparation_steps']


class MyRecipeSerializer(serializers.ModelSerializer):
    """Receita do próprio autor, para criar e editar pela API.

    Segue as regras do painel (recipes/validation.py). Autor, slug e
    publicação são definidos pelo servidor: o que vier no JSON para esses
    campos é ignorado.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name='api:my-recipe-detail',
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        error_messages={'does_not_exist': 'Categoria não encontrada.'},
    )
    preparation_time_unit = serializers.ChoiceField(
        choices=validation.TIME_UNITS,
    )
    servings_unit = serializers.ChoiceField(choices=validation.SERVINGS_UNITS)
    cover = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'url', 'title', 'slug', 'description', 'category',
            'preparation_time', 'preparation_time_unit', 'servings',
            'servings_unit', 'preparation_steps', 'cover', 'is_published',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['slug', 'is_published', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A tradução do DRF diz "Este campo pode não ser nulo", que dá a
        # entender o contrário. Usa a mesma frase do formulário do painel.
        for field in self.fields.values():
            for key in ('required', 'null', 'blank'):
                if key in field.error_messages:
                    field.error_messages[key] = validation.REQUIRED_MESSAGE

    def validate_title(self, title):
        return validation.clean_title(title)

    def validate_preparation_time(self, value):
        return validation.clean_positive(value)

    def validate_servings(self, value):
        return validation.clean_positive(value)

    def validate_cover(self, cover):
        return validation.clean_cover(cover)

    def validate(self, attrs):
        # No PATCH pode vir só um dos dois; compara com o que está salvo.
        current = self.instance
        title = attrs.get('title', current.title if current else '')
        description = attrs.get(
            'description', current.description if current else '',
        )
        error = validation.check_description(title, description)
        if error:
            raise serializers.ValidationError({'description': [error]})
        return attrs
