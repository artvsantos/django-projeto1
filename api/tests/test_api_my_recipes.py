import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from parameterized import parameterized
from PIL import Image
from rest_framework import status
from rest_framework.authtoken.models import Token

from recipes.models import Recipe

from .test_api_recipes import ApiTestBase

MEDIA_DE_TESTE = tempfile.mkdtemp()


def make_image(name='capa.png', padding=0):
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), 'orange').save(buffer, 'PNG')
    return SimpleUploadedFile(
        name, buffer.getvalue() + b'\0' * padding, content_type='image/png',
    )


@override_settings(MEDIA_ROOT=MEDIA_DE_TESTE)
class MyRecipesApiTestBase(ApiTestBase):
    url = '/api/v1/my-recipes/'

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_DE_TESTE, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.other = User.objects.create_user(username='joao', password='x')
        token = Token.objects.create(user=self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def payload(self, **kwargs):
        data = {
            'title': 'Bolo de cenoura',
            'description': 'Com calda de chocolate por cima',
            'category': self.category.pk,
            'preparation_time': 50,
            'preparation_time_unit': 'minutos',
            'servings': 10,
            'servings_unit': 'fatias',
            'preparation_steps': 'Bata no liquidificador e asse.',
        }
        data.update(kwargs)
        return data

    def detail(self, recipe):
        return f'{self.url}{recipe.pk}/'


class MyRecipesAccessTest(MyRecipesApiTestBase):
    def test_urls_are_correct(self):
        self.assertEqual(reverse('api:my-recipe-list'), self.url)
        self.assertEqual(
            reverse('api:my-recipe-detail', args=[1]),
            '/api/v1/my-recipes/1/',
        )

    def test_without_token_returns_401(self):
        self.client.credentials()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token token-inventado')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_browsable_page_titles_are_in_portuguese(self):
        recipe = self.make_recipe()

        listing = self.client.get(self.url, HTTP_ACCEPT='text/html')
        detail = self.client.get(self.detail(recipe), HTTP_ACCEPT='text/html')

        self.assertContains(listing, '<h1>Minhas receitas</h1>')
        self.assertContains(detail, '<h1>Minha receita</h1>')

    def test_api_root_lists_my_recipes(self):
        response = self.client.get('/api/v1/')

        self.assertEqual(
            response.data['my-recipes'],
            'http://testserver/api/v1/my-recipes/',
        )


class MyRecipesListTest(MyRecipesApiTestBase):
    def test_lists_only_my_recipes_published_or_not(self):
        published = self.make_recipe(title='Já aprovada')
        pending = self.make_recipe(title='Na fila', is_published=False)
        self.make_recipe(title='Receita do João', author=self.other)

        response = self.client.get(self.url)
        items = {
            item['id']: item['is_published']
            for item in response.data['results']
        }

        self.assertEqual(items, {published.pk: True, pending.pk: False})

    def test_item_has_expected_fields(self):
        self.make_recipe()
        item = self.client.get(self.url).data['results'][0]

        self.assertEqual(set(item), {
            'id', 'url', 'title', 'slug', 'description', 'category',
            'preparation_time', 'preparation_time_unit', 'servings',
            'servings_unit', 'preparation_steps', 'cover', 'is_published',
            'created_at', 'updated_at',
        })


class MyRecipesCreateTest(MyRecipesApiTestBase):
    def test_create_saves_unpublished_recipe_for_token_owner(self):
        response = self.client.post(self.url, self.payload())
        recipe = Recipe.objects.get(pk=response.data['id'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipe.author, self.author)
        self.assertFalse(recipe.is_published)
        self.assertEqual(recipe.slug, 'bolo-de-cenoura')
        self.assertFalse(response.data['is_published'])

    def test_author_cannot_publish_or_send_html_on_his_own(self):
        response = self.client.post(self.url, self.payload(
            is_published=True, preparation_steps_is_html=True,
            author=self.other.pk, slug='slug-escolhido',
        ))
        recipe = Recipe.objects.get(pk=response.data['id'])

        self.assertFalse(recipe.is_published)
        self.assertFalse(recipe.preparation_steps_is_html)
        self.assertEqual(recipe.author, self.author)
        self.assertEqual(recipe.slug, 'bolo-de-cenoura')

    def test_recipe_created_by_api_is_hidden_from_public_api(self):
        recipe_id = self.client.post(self.url, self.payload()).data['id']
        self.client.credentials()

        response = self.client.get(f'/api/v1/recipes/{recipe_id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @parameterized.expand([
        ('title', 'Bolo', 'O título precisa ter pelo menos 5 caracteres.'),
        ('preparation_time', 0, 'Informe um número maior que zero.'),
        ('servings', -3, 'Informe um número maior que zero.'),
        ('preparation_time_unit', 'séculos',
         '"séculos" não é uma escolha válida.'),
        # A tradução do DRF para esses dois casos diz "pode não ser
        # nulo", que dá a entender o contrário; a API usa a do formulário.
        ('category', '', 'Este campo é obrigatório.'),
        ('preparation_steps', '', 'Este campo é obrigatório.'),
    ])
    def test_create_validates_fields_in_portuguese(self, field, value, msg):
        response = self.client.post(self.url, self.payload(**{field: value}))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Recipe.objects.exists())
        self.assertIn(msg, ' '.join(map(str, response.data[field])))

    def test_missing_required_field_says_it_is_required(self):
        data = self.payload()
        del data['title']

        response = self.client.post(self.url, data)

        self.assertEqual(
            list(map(str, response.data['title'])),
            ['Este campo é obrigatório.'],
        )

    def test_description_cannot_be_equal_to_title(self):
        response = self.client.post(self.url, self.payload(
            title='Bolo de cenoura', description='bolo de cenoura',
        ))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            list(map(str, response.data['description'])),
            ['A descrição não pode ser igual ao título.'],
        )

    def test_create_with_cover_by_multipart(self):
        response = self.client.post(
            self.url, self.payload(cover=make_image()), format='multipart',
        )
        recipe = Recipe.objects.get(pk=response.data['id'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(recipe.cover.name.endswith('.png'))
        self.assertTrue(response.data['cover'].startswith('http://testserver/'))

    def test_create_rejects_cover_bigger_than_2mb(self):
        big = make_image(padding=2 * 1024 * 1024)
        response = self.client.post(
            self.url, self.payload(cover=big), format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            list(map(str, response.data['cover'])),
            ['A imagem pode ter no máximo 2 MB.'],
        )


class MyRecipesUpdateDeleteTest(MyRecipesApiTestBase):
    def test_patch_updates_and_sends_recipe_back_to_approval(self):
        recipe = self.make_recipe(slug='bolo-de-fuba', is_published=True)

        response = self.client.patch(
            self.detail(recipe), {'title': 'Bolo de fubá cremoso'},
        )
        recipe.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, 'Bolo de fubá cremoso')
        self.assertEqual(recipe.slug, 'bolo-de-fuba')
        self.assertFalse(recipe.is_published)

    def test_patch_still_validates(self):
        recipe = self.make_recipe()

        response = self.client.patch(self.detail(recipe), {'servings': 0})
        recipe.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(recipe.servings, 8)

    def test_patch_checks_description_against_the_saved_title(self):
        recipe = self.make_recipe(title='Bolo de fubá')

        response = self.client.patch(
            self.detail(recipe), {'description': 'Bolo de fubá'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_replaces_the_recipe(self):
        recipe = self.make_recipe()

        response = self.client.put(
            self.detail(recipe), self.payload(title='Bolo de laranja'),
        )
        recipe.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, 'Bolo de laranja')

    def test_delete_removes_my_recipe(self):
        recipe = self.make_recipe()

        response = self.client.delete(self.detail(recipe))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(pk=recipe.pk).exists())

    @parameterized.expand(['get', 'patch', 'put', 'delete'])
    def test_recipe_from_another_author_is_404(self, method):
        recipe = self.make_recipe(author=self.other, title='Do João')

        response = getattr(self.client, method)(
            self.detail(recipe), self.payload(title='Hackeado'),
        )
        recipe.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(recipe.title, 'Do João')
