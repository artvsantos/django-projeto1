"""A foto da receita sai do armazenamento junto com ela.

Sem isso, apagar a receita ou trocar a foto deixava o arquivo antigo
esquecido (no Cloudinary, acessível por quem tivesse o endereço).
"""
import io
import shutil
import tempfile
from unittest import mock

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from .test_recipe_base import Recipe, RecipeTestBase

MEDIA_DE_TESTE = tempfile.mkdtemp()


def make_image(name='capa.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), 'orange').save(buffer, 'PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), 'image/png')


@override_settings(MEDIA_ROOT=MEDIA_DE_TESTE)
class RecipeCoverCleanupTest(RecipeTestBase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_DE_TESTE, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.recipe = self.make_recipe()
        with self.captureOnCommitCallbacks(execute=True):
            self.recipe.cover = make_image('antiga.png')
            self.recipe.save()
        self.old_name = self.recipe.cover.name

    def test_cover_file_is_saved(self):
        self.assertTrue(default_storage.exists(self.old_name))

    def test_deleting_recipe_deletes_its_cover(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.recipe.delete()

        self.assertFalse(default_storage.exists(self.old_name))

    def test_replacing_cover_deletes_the_old_file(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.recipe.cover = make_image('nova.png')
            self.recipe.save()

        self.assertFalse(default_storage.exists(self.old_name))
        self.assertTrue(default_storage.exists(self.recipe.cover.name))

    def test_clearing_cover_deletes_the_old_file(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.recipe.cover = ''
            self.recipe.save()

        self.assertFalse(default_storage.exists(self.old_name))

    def test_saving_without_touching_cover_keeps_the_file(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.recipe.title = 'Outro título'
            self.recipe.save()

        self.assertTrue(default_storage.exists(self.old_name))

    def test_file_is_kept_if_the_save_is_rolled_back(self):
        # A foto só some depois que o banco confirmou a troca. Se algo
        # der errado no meio, a receita continua apontando para ela.
        try:
            with transaction.atomic():
                self.recipe.cover = make_image('nova.png')
                self.recipe.save()
                raise RuntimeError('falha no meio do caminho')
        except RuntimeError:
            pass

        self.assertTrue(default_storage.exists(self.old_name))

    def test_new_recipe_with_cover_deletes_nothing(self):
        with self.captureOnCommitCallbacks(execute=True):
            other = self.make_recipe(
                slug='outra', author_data={'username': 'outro'},
            )
            other.cover = make_image('outra.png')
            other.save()

        self.assertTrue(default_storage.exists(self.old_name))
        self.assertTrue(default_storage.exists(other.cover.name))

    def test_recipe_saved_with_unused_id_deletes_nothing(self):
        # Acontece ao importar dados: a receita já chega com id, mas
        # ainda não existe no banco, então não há foto antiga.
        imported = Recipe(
            pk=99999, title='Receita importada', slug='importada',
            description='Veio de outro sistema', preparation_time=5,
            preparation_time_unit='minutos', servings=2,
            servings_unit='porções', preparation_steps='Sirva.',
            cover=make_image('importada.png'),
        )
        with self.captureOnCommitCallbacks(execute=True):
            imported.save()

        self.assertTrue(default_storage.exists(self.old_name))
        self.assertTrue(default_storage.exists(imported.cover.name))

    def test_storage_failure_does_not_break_the_delete(self):
        # Apagar no Cloudinary é uma chamada de rede. Se ela falhar, a
        # receita já foi apagada no banco: o certo é registrar no log, não
        # mostrar erro 500 para quem clicou em "Apagar".
        storage = self.recipe.cover.storage
        with mock.patch.object(storage, 'delete', side_effect=OSError('rede')):
            with self.assertLogs('recipes.signals', level='WARNING') as logs:
                with self.captureOnCommitCallbacks(execute=True):
                    self.recipe.delete()

        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())
        self.assertIn(self.old_name, logs.output[0])

    def test_author_replacing_photo_in_dashboard_deletes_old_file(self):
        self.client.force_login(self.recipe.author)
        url = reverse('authors:recipe_edit', args=[self.recipe.pk])

        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url, data={
                'title': self.recipe.title,
                'description': 'Descrição nova da receita',
                'category': self.recipe.category.pk,
                'preparation_time': 10,
                'preparation_time_unit': 'minutos',
                'servings': 4,
                'servings_unit': 'porções',
                'preparation_steps': 'Misture tudo.',
                'cover': make_image('do-painel.png'),
            })
        self.recipe.refresh_from_db()

        self.assertIn('do-painel', self.recipe.cover.name)
        self.assertFalse(default_storage.exists(self.old_name))

    def test_author_deleting_in_dashboard_deletes_the_file(self):
        self.client.force_login(self.recipe.author)
        url = reverse('authors:recipe_delete', args=[self.recipe.pk])

        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url)

        self.assertFalse(default_storage.exists(self.old_name))
