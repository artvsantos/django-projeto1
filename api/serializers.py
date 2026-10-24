from rest_framework import serializers

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
