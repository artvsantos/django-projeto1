# Recipes

Site de receitas feito em Django. É um projeto de estudo, escrito com TDD: os testes vieram antes do código.

**No ar:** https://receitas-arthur.onrender.com<br>
<sub>A primeira visita pode levar até um minuto: o servidor gratuito dorme quando fica parado.</sub>

[![CI](https://github.com/artvsantos/django-projeto1/actions/workflows/ci.yml/badge.svg)](https://github.com/artvsantos/django-projeto1/actions/workflows/ci.yml)
[![Django](https://img.shields.io/badge/django-5.2-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com)
[![Cobertura](https://img.shields.io/badge/cobertura-99%25-2EA043?style=flat-square)](#testes)
[![MIT](https://img.shields.io/badge/licença-MIT-blue?style=flat-square)](LICENSE)

[English version](README.en.md)

![Home do Recipes: cabeçalho com links para entrar e criar conta, menu de categorias, busca e a lista de receitas em cards](docs/home.png)

## O que ele faz

- Home com as receitas publicadas, paginada
- Busca por título ou descrição
- Listagem por categoria
- Página de cada receita
- Admin do Django para cadastrar receita e categoria, com upload de capa
- Cadastro de autor, com validação de senha forte e e-mail único
- Login e logout, com proteção contra redirecionamento para outro site
- Painel do autor: cada um envia, edita e apaga as próprias receitas, que só vão ao ar depois de aprovadas no admin
- API REST de leitura em `/api/v1/` (veja abaixo)

A paginação não é a do Django pura. Tem uma função em `utils/pagination.py` que monta o intervalo de páginas em volta da página atual sem passar do começo nem do fim da lista. É a parte com mais caso de borda do projeto, e também a mais testada.

## API

API REST só de leitura, feita com Django REST Framework, aberta a qualquer visitante. Aberta no navegador, mostra uma página navegável; com `curl` ou de outro programa, responde JSON.

| Endereço | O que devolve |
| --- | --- |
| `GET /api/v1/recipes/` | Receitas publicadas, 10 por página. Filtros: `?search=bolo` e `?category=1` |
| `GET /api/v1/recipes/<id>/` | Uma receita, com o modo de preparo |
| `GET /api/v1/categories/` | Categorias com receitas publicadas e quantas cada uma tem |

```bash
curl "https://receitas-arthur.onrender.com/api/v1/recipes/?search=queijo"
```

Receita não publicada dá 404, os dados privados do autor (e-mail, senha) nunca aparecem, e a lista faz sempre 2 consultas ao banco, não importa quantas receitas tenha na página. Tudo isso tem teste.

## Testes

169 testes, 99% de cobertura.

Cobrem os models, as URLs, as views, os formulários, as permissões do painel (ninguém mexe na receita de outro autor) e o cálculo da paginação. Models, views e URLs estão em 100%; a paginação fica em 93%, e é onde moram os casos de borda.

A medição exclui settings, migrations e o comando de seed. Não é código de aplicação, e contar esses arquivos só inflaria o número.

Uso `parameterized` para checar vários campos sem escrever o mesmo teste cinco vezes, e o `Faker` monta as receitas de teste através de uma factory em `utils/recipes/factory.py`.

```bash
pytest

coverage run -m pytest
coverage report
coverage html   # relatório navegável em htmlcov/index.html
```

## Stack

Python 3.11, Django 5.2, Django REST Framework, SQLite, pytest, coverage, python-dotenv, Pillow. Em produção: Postgres, WhiteNoise, gunicorn e Cloudinary para as fotos.

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
authors/          cadastro, login, logout e painel do autor
  forms.py        RegisterForm, LoginForm e RecipeForm
  views.py        conta e painel (criar, editar, apagar receita)
api/              API REST (Django REST Framework)
  serializers.py  o formato do JSON
  views.py        receitas e categorias, só leitura
utils/
  pagination.py   cálculo do intervalo de páginas
  recipes/        factory de receitas falsas
base_templates/   template base
base_static/      css global
```

## Licença

MIT. Veja o [LICENSE](LICENSE).
