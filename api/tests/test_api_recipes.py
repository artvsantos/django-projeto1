from django.contrib.auth.models import User
from django.urls import resolve, reverse
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from api import views
from recipes.models import Category, Recipe


class ApiTestBase(APITestCase):
    def setUp(self) -> None:
        self.author = User.objects.create_user(
            username='mariasouza', first_name='Maria', last_name='Souza',
            email='maria@email.com', password='x',
        )
        self.category = Category.objects.create(name='Sobremesas')
        return super().setUp()

    def make_recipe(self, title='Bolo de fubá', **kwargs):
        data = {
            'title': title,
            'description': 'Bolo fofinho para o café da tarde',
            'preparation_time': 40,
            'preparation_time_unit': 'minutos',
            'servings': 8,
            'servings_unit': 'fatias',
            'preparation_steps': 'Misture tudo e asse.',
            'category': self.category,
            'author': self.author,
            'is_published': True,
        }
        data.update(kwargs)
        return Recipe.objects.create(**data)


class RecipeListApiTest(ApiTestBase):
    url = '/api/v1/recipes/'

    def test_urls_are_correct(self):
        self.assertEqual(reverse('api:recipe-list'), '/api/v1/recipes/')
        self.assertEqual(
            reverse('api:recipe-detail', args=[1]), '/api/v1/recipes/1/',
        )

    def test_list_uses_recipe_viewset(self):
        self.assertIs(
            resolve(self.url).func.cls, views.RecipeViewSet,
        )

    def test_list_returns_only_published_recipes_newest_first(self):
        old = self.make_recipe(title='Receita antiga')
        new = self.make_recipe(title='Receita nova')
        self.make_recipe(title='Ainda na fila', is_published=False)

        response = self.client.get(self.url)
        ids = [item['id'] for item in response.data['results']]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ids, [new.pk, old.pk])

    def test_list_item_has_expected_fields(self):
        recipe = self.make_recipe()
        item = self.client.get(self.url).data['results'][0]

        self.assertEqual(set(item), {
            'id', 'url', 'title', 'slug', 'description', 'category',
            'author', 'preparation_time', 'preparation_time_unit',
            'servings', 'servings_unit', 'cover', 'created_at',
        })
        self.assertEqual(item['category'], {
            'id': self.category.pk, 'name': 'Sobremesas',
        })
        self.assertEqual(item['author'], 'Maria Souza')
        self.assertEqual(
            item['url'], f'http://testserver/api/v1/recipes/{recipe.pk}/',
        )

    def test_list_does_not_send_preparation_steps(self):
        self.make_recipe()
        item = self.client.get(self.url).data['results'][0]

        self.assertNotIn('preparation_steps', item)

    def test_author_without_full_name_shows_username(self):
        self.author.first_name = self.author.last_name = ''
        self.author.save()
        self.make_recipe()

        item = self.client.get(self.url).data['results'][0]

        self.assertEqual(item['author'], 'mariasouza')

    def test_recipe_without_author_or_category_returns_null(self):
        self.make_recipe(author=None, category=None)
        item = self.client.get(self.url).data['results'][0]

        self.assertIsNone(item['author'])
        self.assertIsNone(item['category'])

    def test_cover_is_an_absolute_url_or_null(self):
        with_cover = self.make_recipe(title='Com foto')
        Recipe.objects.filter(pk=with_cover.pk).update(
            cover='recipes/covers/capa.jpg',
        )
        self.make_recipe(title='Sem foto')

        items = {
            item['title']: item['cover']
            for item in self.client.get(self.url).data['results']
        }

        self.assertEqual(
            items['Com foto'],
            'http://testserver/media/recipes/covers/capa.jpg',
        )
        self.assertIsNone(items['Sem foto'])

    def test_author_private_data_never_leaves_the_api(self):
        self.make_recipe()
        content = self.client.get(self.url).content.decode('utf-8')

        self.assertNotIn('maria@email.com', content)
        self.assertNotIn('password', content)

    def test_list_is_paginated_with_10_per_page(self):
        for number in range(12):
            self.make_recipe(title=f'Receita número {number}')

        first = self.client.get(self.url).data
        second = self.client.get(first['next']).data

        self.assertEqual(first['count'], 12)
        self.assertEqual(len(first['results']), 10)
        self.assertIsNone(first['previous'])
        self.assertEqual(len(second['results']), 2)
        self.assertIsNone(second['next'])

    def test_list_query_count_does_not_grow_with_recipes(self):
        # Sem select_related, cada receita faria 2 consultas a mais (autor
        # e categoria). Com 10 por página seriam 22 em vez de 2.
        for number in range(10):
            self.make_recipe(title=f'Receita número {number}')

        with self.assertNumQueries(2):  # contagem + página
            self.client.get(self.url)

    def test_search_finds_title_or_description_ignoring_case(self):
        by_title = self.make_recipe(title='Pudim de leite')
        by_description = self.make_recipe(
            title='Sobremesa gelada', description='Leva leite condensado',
        )
        self.make_recipe(title='Feijoada', description='Prato principal')

        response = self.client.get(self.url, {'search': 'LEITE'})
        ids = {item['id'] for item in response.data['results']}

        self.assertEqual(ids, {by_title.pk, by_description.pk})

    def test_filter_by_category(self):
        lanches = Category.objects.create(name='Lanches')
        snack = self.make_recipe(title='Pão de queijo', category=lanches)
        self.make_recipe(title='Pudim de leite')

        response = self.client.get(self.url, {'category': lanches.pk})
        ids = [item['id'] for item in response.data['results']]

        self.assertEqual(ids, [snack.pk])

    def test_invalid_category_filter_returns_400_in_portuguese(self):
        response = self.client.get(self.url, {'category': 'abc'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {'category': 'Informe o id numérico da categoria.'},
        )

    @parameterized.expand(['post', 'put', 'patch', 'delete'])
    def test_api_is_read_only(self, method):
        recipe = self.make_recipe()
        detail = f'/api/v1/recipes/{recipe.pk}/'
        url = self.url if method == 'post' else detail

        response = getattr(self.client, method)(url, {'title': 'Hackeado'})
        recipe.refresh_from_db()

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(recipe.title, 'Bolo de fubá')


class RecipeDetailApiTest(ApiTestBase):
    def test_detail_includes_preparation_steps(self):
        recipe = self.make_recipe()
        response = self.client.get(f'/api/v1/recipes/{recipe.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['preparation_steps'], 'Misture tudo e asse.',
        )
        self.assertEqual(response.data['title'], 'Bolo de fubá')

    def test_unpublished_recipe_is_404(self):
        recipe = self.make_recipe(is_published=False)
        response = self.client.get(f'/api/v1/recipes/{recipe.pk}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_recipe_is_404(self):
        response = self.client.get('/api/v1/recipes/99999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ApiRootTest(ApiTestBase):
    def test_root_lists_the_endpoints(self):
        response = self.client.get('/api/v1/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'recipes': 'http://testserver/api/v1/recipes/',
            'categories': 'http://testserver/api/v1/categories/',
        })

    def test_browsable_api_page_opens_in_the_browser(self):
        response = self.client.get('/api/v1/recipes/', HTTP_ACCEPT='text/html')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/html', response['Content-Type'])

    @parameterized.expand([
        ('/api/v1/', 'API do Receitas', 'Api Root'),
        ('/api/v1/recipes/', 'Receitas', 'Recipe List'),
        ('/api/v1/categories/', 'Categorias', 'Category List'),
    ])
    def test_browsable_api_titles_are_in_portuguese(self, url, title, old):
        response = self.client.get(url, HTTP_ACCEPT='text/html')
        content = response.content.decode('utf-8')

        self.assertIn(f'<h1>{title}</h1>', content)
        self.assertNotIn(old, content)

    def test_browsable_recipe_detail_title_is_in_portuguese(self):
        recipe = self.make_recipe()
        response = self.client.get(
            f'/api/v1/recipes/{recipe.pk}/', HTTP_ACCEPT='text/html',
        )

        self.assertIn('<h1>Receita</h1>', response.content.decode('utf-8'))
