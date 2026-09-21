from recipes.context_processors import menu_categories
from recipes.tests.test_recipe_base import RecipeTestBase


class MenuCategoriesTest(RecipeTestBase):
    def test_menu_shows_category_that_has_published_recipe(self):
        self.make_recipe(category_data={'name': 'Sobremesas'})
        nomes = [c.name for c in menu_categories(None)['menu_categories']]
        self.assertIn('Sobremesas', nomes)

    def test_menu_hides_category_with_only_unpublished_recipe(self):
        self.make_recipe(
            category_data={'name': 'Rascunhos'}, is_published=False)
        nomes = [c.name for c in menu_categories(None)['menu_categories']]
        self.assertNotIn('Rascunhos', nomes)

    def test_menu_does_not_repeat_category_with_many_recipes(self):
        primeira = self.make_recipe(
            category_data={'name': 'Lanches'}, slug='um',
            author_data={'username': 'a'})

        # a segunda receita aponta para a MESMA categoria, que e o caso
        # em que o distinct() do context processor faz diferenca
        segunda = self.make_recipe(slug='dois', author_data={'username': 'b'})
        segunda.category = primeira.category
        segunda.save()

        nomes = [c.name for c in menu_categories(None)['menu_categories']]
        self.assertEqual(nomes.count('Lanches'), 1)

    def test_menu_is_empty_when_there_is_no_recipe(self):
        self.assertEqual(
            list(menu_categories(None)['menu_categories']), [])
