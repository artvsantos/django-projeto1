"""Popula o banco com receitas de exemplo, para desenvolvimento e screenshots.

Uso:
    python manage.py seed_recipes
    python manage.py seed_recipes --refazer   # apaga as de exemplo e cria de novo

As capas sao lidas da pasta seed_images/ na raiz do projeto, casando pelo
nome do arquivo (ex.: bolo-de-cenoura.jpg). Receita sem imagem correspondente
e criada sem capa.
"""
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from recipes.models import Category, Recipe

RECEITAS = [
    {
        'title': 'Bolo de cenoura com calda de chocolate',
        'category': 'Sobremesas',
        'description': (
            'O bolo de domingo da infância: massa fofa de cenoura e uma '
            'calda de chocolate que endurece levemente por cima.'
        ),
        'preparation_time': 50,
        'preparation_time_unit': 'minutos',
        'servings': 12,
        'servings_unit': 'fatias',
        'preparation_steps': (
            'Bata no liquidificador a cenoura, os ovos e o óleo até ficar liso.\n'
            'Misture o açúcar e a farinha em uma tigela e junte o líquido.\n'
            'Acrescente o fermento por último, mexendo devagar.\n'
            'Asse a 180 graus por cerca de 40 minutos.\n'
            'Leve a calda ao fogo até engrossar e despeje sobre o bolo morno.'
        ),
    },
    {
        'title': 'Strogonoff de frango',
        'category': 'Pratos principais',
        'description': (
            'Cremoso, rápido e resolve o jantar de qualquer terça-feira. '
            'Vai bem com arroz branco e batata palha.'
        ),
        'preparation_time': 35,
        'preparation_time_unit': 'minutos',
        'servings': 4,
        'servings_unit': 'porções',
        'preparation_steps': (
            'Corte o frango em cubos e tempere com sal, alho e pimenta.\n'
            'Doure em fogo alto até criar cor, sem mexer demais.\n'
            'Junte a cebola, o ketchup e a mostarda e cozinhe dois minutos.\n'
            'Desligue o fogo antes de adicionar o creme de leite.\n'
            'Sirva com arroz e batata palha por cima.'
        ),
    },
    {
        'title': 'Feijoada de panela de pressão',
        'category': 'Pratos principais',
        'description': (
            'A versão de fim de semana sem passar o dia inteiro na cozinha. '
            'O segredo está em dessalgar as carnes na véspera.'
        ),
        'preparation_time': 2,
        'preparation_time_unit': 'horas',
        'servings': 8,
        'servings_unit': 'porções',
        'preparation_steps': (
            'Deixe as carnes salgadas de molho por doze horas, trocando a água.\n'
            'Cozinhe o feijão preto na pressão por vinte minutos.\n'
            'Frite o alho e a cebola e refogue as carnes.\n'
            'Junte tudo e volte à pressão por mais trinta minutos.\n'
            'Sirva com arroz, couve refogada e laranja.'
        ),
    },
    {
        'title': 'Pão de queijo mineiro',
        'category': 'Lanches',
        'description': (
            'Casquinha fina por fora e puxento por dentro. Rende bastante e '
            'pode congelar cru para assar depois.'
        ),
        'preparation_time': 40,
        'preparation_time_unit': 'minutos',
        'servings': 25,
        'servings_unit': 'unidades',
        'preparation_steps': (
            'Ferva o leite com o óleo e o sal e escalde o polvilho.\n'
            'Deixe amornar e sove até a massa ficar homogênea.\n'
            'Junte os ovos um a um, sovando entre cada um.\n'
            'Acrescente o queijo meia cura ralado.\n'
            'Enrole as bolinhas e asse a 200 graus por 25 minutos.'
        ),
    },
]


class Command(BaseCommand):
    help = 'Cria receitas de exemplo para desenvolvimento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refazer',
            action='store_true',
            help='Apaga as receitas de exemplo antes de criar, para reanexar '
                 'as capas depois de colocar as fotos em seed_images/',
        )

    def handle(self, *args, **options):
        autor = User.objects.order_by('id').first()
        if autor is None:
            self.stdout.write(self.style.ERROR(
                'Nenhum usuario encontrado. Rode antes: '
                'python manage.py createsuperuser'
            ))
            return

        slugs = [slugify(dados['title']) for dados in RECEITAS]

        if options['refazer']:
            apagadas, _ = Recipe.objects.filter(slug__in=slugs).delete()
            self.stdout.write(self.style.WARNING(
                f'  {apagadas} registro(s) de exemplo apagado(s)'))

        pasta_imagens = Path(__file__).resolve().parents[3] / 'seed_images'
        criadas = 0

        for dados in RECEITAS:
            slug = slugify(dados['title'])
            if Recipe.objects.filter(slug=slug).exists():
                self.stdout.write(f'  ja existe: {dados["title"]}')
                continue

            categoria, _ = Category.objects.get_or_create(
                name=dados['category'])

            receita = Recipe(
                title=dados['title'],
                description=dados['description'],
                slug=slug,
                preparation_time=dados['preparation_time'],
                preparation_time_unit=dados['preparation_time_unit'],
                servings=dados['servings'],
                servings_unit=dados['servings_unit'],
                preparation_steps=dados['preparation_steps'],
                is_published=True,
                category=categoria,
                author=autor,
            )

            imagem = self._procurar_imagem(pasta_imagens, slug)
            if imagem is not None:
                with imagem.open('rb') as arquivo:
                    receita.cover.save(imagem.name, File(arquivo), save=False)
            else:
                self.stdout.write(self.style.WARNING(
                    f'  sem imagem para {slug} (procurei em seed_images/)'))

            receita.save()
            criadas += 1
            self.stdout.write(self.style.SUCCESS(f'  criada: {receita.title}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nPronto. {criadas} receita(s) criada(s).'))

    @staticmethod
    def _procurar_imagem(pasta, slug):
        if not pasta.is_dir():
            return None
        for extensao in ('jpg', 'jpeg', 'png', 'webp'):
            caminho = pasta / f'{slug}.{extensao}'
            if caminho.is_file():
                return caminho
        return None
