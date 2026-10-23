"""Páginas de erro que o visitante vê no site no ar (DEBUG desligado).

O test runner do Django já roda com DEBUG=False, então o 404 daqui é o
mesmo da produção.
"""
from django.test import RequestFactory, TestCase
from django.views.defaults import server_error


class NotFoundPageTest(TestCase):
    def test_unknown_url_shows_portuguese_404_page(self):
        response = self.client.get('/pagina-que-nao-existe/')

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(
            response, 'Página não encontrada', status_code=404,
        )

    def test_missing_recipe_uses_the_same_404_page(self):
        response = self.client.get('/recipes/99999/')

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')

    def test_404_page_keeps_site_layout_and_link_home(self):
        response = self.client.get('/pagina-que-nao-existe/')

        self.assertTemplateUsed(response, 'global/base.html')
        self.assertContains(response, 'href="/"', status_code=404)

    def test_404_page_does_not_echo_the_requested_path(self):
        # Mostrar o endereço digitado abre espaço para phishing do tipo
        # "/sua-conta-foi-bloqueada-ligue-para-...".
        response = self.client.get('/ligue-para-0800-123/')

        self.assertNotContains(
            response, 'ligue-para-0800-123', status_code=404,
        )


class ServerErrorPageTest(TestCase):
    def test_500_page_is_in_portuguese(self):
        request = RequestFactory().get('/')
        response = server_error(request)

        self.assertEqual(response.status_code, 500)
        self.assertIn('Algo deu errado', response.content.decode('utf-8'))

    def test_500_page_does_not_touch_the_database(self):
        # Se o erro foi o banco fora do ar, a página de erro não pode
        # depender dele (o menu de categorias consulta o banco).
        request = RequestFactory().get('/')

        with self.assertNumQueries(0):
            server_error(request)
