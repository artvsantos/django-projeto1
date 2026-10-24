from django.urls import reverse
from rest_framework import status

from recipes.models import Category

from .test_api_recipes import ApiTestBase


class CategoryApiTest(ApiTestBase):
    url = '/api/v1/categories/'

    def test_url_is_correct(self):
        self.assertEqual(reverse('api:category-list'), self.url)

    def test_lists_only_categories_with_published_recipes(self):
        lanches = Category.objects.create(name='Lanches')
        Category.objects.create(name='Vazia')
        hidden = Category.objects.create(name='Só rascunho')
        self.make_recipe(title='Pudim de leite')
        self.make_recipe(title='Pão de queijo', category=lanches)
        self.make_recipe(title='Na fila', category=hidden, is_published=False)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            {'id': lanches.pk, 'name': 'Lanches', 'recipes_count': 1},
            {'id': self.category.pk, 'name': 'Sobremesas', 'recipes_count': 1},
        ])

    def test_recipes_count_ignores_unpublished(self):
        self.make_recipe(title='Pudim de leite')
        self.make_recipe(title='Bolo de cenoura')
        self.make_recipe(title='Na fila', is_published=False)

        item = self.client.get(self.url).data[0]

        self.assertEqual(item['recipes_count'], 2)

    def test_categories_are_read_only(self):
        response = self.client.post(self.url, {'name': 'Nova'})

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
        )
