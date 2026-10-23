"""Settings que mudam conforme as variáveis de ambiente da hospedagem.

O settings é lido uma vez só por processo, então cada cenário roda num
Python separado, com o ambiente montado aqui.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SCRIPT = """
import json, django
django.setup()
from django.conf import settings
from django.core.files.storage import storages
from django.core.management import get_commands
print(json.dumps({
    'collectstatic_from': get_commands()['collectstatic'],
    'storage': type(storages['default']).__name__,
    'apps': settings.INSTALLED_APPS,
    'db_health_checks': settings.DATABASES['default']['CONN_HEALTH_CHECKS'],
}))
"""


def load_settings(**env_vars):
    env = {
        key: value for key, value in os.environ.items()
        if key not in ('CLOUDINARY_URL', 'DATABASE_URL', 'PRODUCTION')
    }
    env.update(DJANGO_SETTINGS_MODULE='projeto.settings', **env_vars)
    result = subprocess.run(
        [sys.executable, '-c', SCRIPT],
        cwd=BASE_DIR, env=env, capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


class MediaStorageSettingsTest(SimpleTestCase):
    def test_without_cloudinary_url_uploads_stay_on_local_disk(self):
        config = load_settings()

        self.assertEqual(config['storage'], 'FileSystemStorage')
        self.assertNotIn('cloudinary_storage', config['apps'])

    def test_with_cloudinary_url_uploads_go_to_cloudinary(self):
        config = load_settings(CLOUDINARY_URL='cloudinary://123:abc@demo')

        self.assertEqual(config['storage'], 'MediaCloudinaryStorage')
        self.assertIn('cloudinary_storage', config['apps'])
        self.assertIn('cloudinary', config['apps'])

    def test_collectstatic_stays_the_one_from_django(self):
        # O pacote traz um collectstatic próprio que quebra no Django 5.2
        # (procura STATICFILES_STORAGE, que não existe mais). O CSS segue
        # com o WhiteNoise; o Cloudinary cuida só das fotos.
        config = load_settings(CLOUDINARY_URL='cloudinary://123:abc@demo')

        self.assertEqual(
            config['collectstatic_from'], 'django.contrib.staticfiles',
        )


class DatabaseSettingsTest(SimpleTestCase):
    def test_database_checks_connection_before_reusing_it(self):
        # O banco gratuito desliga quando fica parado; sem a checagem, a
        # primeira visita depois disso tentaria usar uma conexão morta.
        config = load_settings()

        self.assertTrue(config['db_health_checks'])
