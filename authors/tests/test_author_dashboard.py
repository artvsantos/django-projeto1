import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import resolve, reverse
from parameterized import parameterized
from PIL import Image

from authors import views
from recipes.models import Category, Recipe

MEDIA_DE_TESTE = tempfile.mkdtemp()


def make_image(name='capa.png', padding=0):
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), 'orange').save(buffer, 'PNG')
    return SimpleUploadedFile(
        name, buffer.getvalue() + b'\0' * padding, content_type='image/png',
    )


@override_settings(MEDIA_ROOT=MEDIA_DE_TESTE)
class DashboardTestBase(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_DE_TESTE, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='mariasouza', first_name='Maria', password='x',
        )
        self.other = User.objects.create_user(username='joao', password='x')
        self.category = Category.objects.create(name='Sobremesas')
        self.client.force_login(self.user)
        return super().setUp()

    def make_recipe(self, author=None, title='Bolo de fubá', **kwargs):
        data = {
            'author': author or self.user,
            'title': title,
            'description': 'Bolo fofinho para o café da tarde',
            'preparation_time': 40,
            'preparation_time_unit': 'minutos',
            'servings': 8,
            'servings_unit': 'fatias',
            'preparation_steps': 'Misture tudo e asse.',
            'category': self.category,
        }
        data.update(kwargs)
        return Recipe.objects.create(**data)

    def form_data(self, **kwargs):
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


class DashboardAccessTest(DashboardTestBase):
    def urls(self, pk=1):
        return [
            reverse('authors:dashboard'),
            reverse('authors:recipe_create'),
            reverse('authors:recipe_edit', args=[pk]),
            reverse('authors:recipe_delete', args=[pk]),
        ]

    def test_dashboard_urls_are_correct(self):
        self.assertEqual(self.urls(), [
            '/authors/dashboard/',
            '/authors/dashboard/recipe/new/',
            '/authors/dashboard/recipe/1/edit/',
            '/authors/dashboard/recipe/1/delete/',
        ])

    def test_anonymous_user_is_sent_to_login(self):
        recipe = self.make_recipe()
        self.client.logout()

        for url in self.urls(recipe.pk):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response, f'/authors/login/?next={url}',
                    fetch_redirect_response=False,
                )


class DashboardListTest(DashboardTestBase):
    def test_dashboard_uses_correct_view_and_template(self):
        url = reverse('authors:dashboard')
        response = self.client.get(url)

        self.assertIs(resolve(url).func, views.dashboard)
        self.assertTemplateUsed(response, 'authors/pages/dashboard.html')

    def test_dashboard_lists_only_my_recipes(self):
        mine = self.make_recipe(title='Minha receita')
        others = self.make_recipe(author=self.other, title='Receita do João')
        response = self.client.get(reverse('authors:dashboard'))

        self.assertIn(mine, response.context['recipes'])
        self.assertNotIn(others, response.context['recipes'])

    def test_dashboard_shows_status_of_each_recipe(self):
        self.make_recipe(title='Já aprovada', is_published=True)
        self.make_recipe(title='Ainda na fila', is_published=False)
        response = self.client.get(reverse('authors:dashboard'))

        self.assertContains(response, 'Publicada')
        self.assertContains(response, 'Aguardando aprovação')

    def test_dashboard_shows_empty_state(self):
        response = self.client.get(reverse('authors:dashboard'))

        self.assertContains(response, 'Você ainda não tem receitas.')

    def test_header_shows_dashboard_link_for_logged_in_user(self):
        response = self.client.get(reverse('recipes:home'))

        self.assertContains(response, reverse('authors:dashboard'))


class RecipeCreateTest(DashboardTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.url = reverse('authors:recipe_create')

    def test_create_loads_form_template(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authors/pages/recipe-form.html')
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_create_saves_recipe_as_unpublished_from_logged_user(self):
        response = self.client.post(self.url, data=self.form_data())
        recipe = Recipe.objects.get()

        self.assertRedirects(response, reverse('authors:dashboard'))
        self.assertEqual(recipe.author, self.user)
        self.assertFalse(recipe.is_published)
        self.assertEqual(recipe.slug, 'bolo-de-cenoura')

    def test_create_shows_message_about_approval(self):
        response = self.client.post(
            self.url, data=self.form_data(), follow=True,
        )

        self.assertContains(
            response, 'Receita enviada! Ela aparece no site depois de aprovada.',
        )

    def test_author_cannot_publish_or_send_html_on_his_own(self):
        self.client.post(self.url, data=self.form_data(
            is_published='on', preparation_steps_is_html='on',
        ))
        recipe = Recipe.objects.get()

        self.assertFalse(recipe.is_published)
        self.assertFalse(recipe.preparation_steps_is_html)

    def test_recipes_with_same_title_get_different_slugs(self):
        self.client.post(self.url, data=self.form_data())
        self.client.post(self.url, data=self.form_data())
        slugs = sorted(Recipe.objects.values_list('slug', flat=True))

        self.assertEqual(slugs, ['bolo-de-cenoura', 'bolo-de-cenoura-2'])

    def test_create_saves_cover_image(self):
        self.client.post(
            self.url, data=self.form_data(cover=make_image()),
        )
        recipe = Recipe.objects.get()

        self.assertTrue(recipe.cover.name.endswith('.png'))

    def test_create_rejects_file_that_is_not_an_image(self):
        fake = SimpleUploadedFile(
            'capa.png', b'nao sou imagem', content_type='image/png',
        )
        response = self.client.post(
            self.url, data=self.form_data(cover=fake),
        )

        self.assertFalse(Recipe.objects.exists())
        self.assertIn('cover', response.context['form'].errors)

    def test_create_rejects_image_bigger_than_2mb(self):
        big = make_image(padding=2 * 1024 * 1024)
        response = self.client.post(self.url, data=self.form_data(cover=big))

        self.assertFalse(Recipe.objects.exists())
        self.assertIn(
            'A imagem pode ter no máximo 2 MB.',
            response.context['form'].errors['cover'],
        )

    @parameterized.expand([
        ('title', 'Bolo', 'O título precisa ter pelo menos 5 caracteres.'),
        ('preparation_time', '0', 'Informe um número maior que zero.'),
        ('servings', '-3', 'Informe um número maior que zero.'),
        ('preparation_time_unit', 'séculos', 'Faça uma escolha válida.'),
        ('category', '', 'Este campo é obrigatório.'),
        ('preparation_steps', '', 'Este campo é obrigatório.'),
    ])
    def test_create_validates_fields(self, field, value, message):
        response = self.client.post(
            self.url, data=self.form_data(**{field: value}),
        )

        self.assertFalse(Recipe.objects.exists())
        errors = ' '.join(response.context['form'].errors[field])
        self.assertIn(message, errors)

    def test_description_cannot_be_equal_to_title(self):
        response = self.client.post(self.url, data=self.form_data(
            title='Bolo de cenoura', description='Bolo de cenoura',
        ))

        self.assertIn(
            'A descrição não pode ser igual ao título.',
            response.context['form'].errors['description'],
        )


class RecipeEditTest(DashboardTestBase):
    def test_edit_shows_form_filled_with_recipe(self):
        recipe = self.make_recipe()
        response = self.client.get(
            reverse('authors:recipe_edit', args=[recipe.pk]),
        )

        self.assertTemplateUsed(response, 'authors/pages/recipe-form.html')
        self.assertContains(response, 'value="Bolo de fubá"')

    def test_edit_updates_recipe_and_keeps_slug(self):
        recipe = self.make_recipe(slug='bolo-de-fuba')
        response = self.client.post(
            reverse('authors:recipe_edit', args=[recipe.pk]),
            data=self.form_data(title='Bolo de fubá cremoso'),
        )
        recipe.refresh_from_db()

        self.assertRedirects(response, reverse('authors:dashboard'))
        self.assertEqual(recipe.title, 'Bolo de fubá cremoso')
        self.assertEqual(recipe.slug, 'bolo-de-fuba')

    def test_editing_published_recipe_sends_it_back_to_approval(self):
        recipe = self.make_recipe(is_published=True)
        response = self.client.post(
            reverse('authors:recipe_edit', args=[recipe.pk]),
            data=self.form_data(), follow=True,
        )
        recipe.refresh_from_db()

        self.assertFalse(recipe.is_published)
        self.assertContains(
            response, 'Receita salva. Ela aparece no site depois de aprovada.',
        )

    def test_cannot_edit_recipe_from_another_author(self):
        recipe = self.make_recipe(author=self.other)
        url = reverse('authors:recipe_edit', args=[recipe.pk])

        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.post(url, data=self.form_data(title='Hackeado'))
        recipe.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(recipe.title, 'Bolo de fubá')


class RecipeDeleteTest(DashboardTestBase):
    def test_delete_with_get_is_not_allowed(self):
        recipe = self.make_recipe()
        response = self.client.get(
            reverse('authors:recipe_delete', args=[recipe.pk]),
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Recipe.objects.filter(pk=recipe.pk).exists())

    def test_delete_removes_my_recipe(self):
        recipe = self.make_recipe()
        response = self.client.post(
            reverse('authors:recipe_delete', args=[recipe.pk]), follow=True,
        )

        self.assertFalse(Recipe.objects.filter(pk=recipe.pk).exists())
        self.assertRedirects(response, reverse('authors:dashboard'))
        self.assertContains(response, 'Receita apagada.')

    def test_cannot_delete_recipe_from_another_author(self):
        recipe = self.make_recipe(author=self.other)
        response = self.client.post(
            reverse('authors:recipe_delete', args=[recipe.pk]),
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Recipe.objects.filter(pk=recipe.pk).exists())
