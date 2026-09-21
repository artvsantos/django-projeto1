# Recipes

Site de receitas feito em Django. É um projeto de estudo, escrito com TDD: os testes vieram antes do código.

[![CI](https://github.com/artvsantos/django-projeto1/actions/workflows/ci.yml/badge.svg)](https://github.com/artvsantos/django-projeto1/actions/workflows/ci.yml)
[![Django](https://img.shields.io/badge/django-5.2-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com)
[![Cobertura](https://img.shields.io/badge/cobertura-99%25-2EA043?style=flat-square)](#testes)
[![MIT](https://img.shields.io/badge/licença-MIT-blue?style=flat-square)](LICENSE)

[English version](README.en.md)

<!-- tire um print da home, salve como docs/home.png e descomente a linha abaixo -->
<!-- ![Home](docs/home.png) -->

## O que ele faz

- Home com as receitas publicadas, paginada
- Busca por título ou descrição
- Listagem por categoria
- Página de cada receita
- Admin do Django para cadastrar receita e categoria, com upload de capa

A paginação não é a do Django pura. Tem uma função em `utils/pagination.py` que monta o intervalo de páginas em volta da página atual sem passar do começo nem do fim da lista. É a parte com mais caso de borda do projeto, e também a mais testada.

## Testes

37 testes, 99% de cobertura.

Cobrem os models, as URLs, as quatro views e o cálculo da paginação. Uso `parameterized` para checar vários campos sem escrever o mesmo teste cinco vezes, e o `Faker` monta as receitas de teste através de uma factory em `utils/recipes/factory.py`.

```bash
pytest

coverage run -m pytest
coverage report
coverage html   # relatório navegável em htmlcov/index.html
```

## Stack

Python 3.11, Django 5.2, SQLite, pytest, coverage, python-dotenv, Pillow.

## Rodando localmente

```bash
git clone https://github.com/artvsantos/django-projeto1.git
cd django-projeto1

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt   # só para rodar os testes

cp .env-exemple .env            # Windows: copy .env-exemple .env
# troque o SECRET_KEY no .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre em http://localhost:8000, e o admin fica em /admin.

Receita só aparece no site com `is_published` marcado.

## Estrutura

```
projeto/          settings, urls, wsgi/asgi
recipes/          app principal
  models.py       Recipe e Category
  views.py        home, search, category, recipe
  tests/          os testes
  templates/      páginas e partials
utils/
  pagination.py   cálculo do intervalo de páginas
  recipes/        factory de receitas falsas
base_templates/   template base
base_static/      css global
```

## Licença

MIT. Veja o [LICENSE](LICENSE).
