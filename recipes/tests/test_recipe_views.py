
from django.urls import reverse, resolve
from recipes import views
from .test_recipe_base import RecipeTestBase

# Create your tests here.


class RecipeViewsTest(RecipeTestBase):

    def test_recipe_home_view_func_is_correct(self):
        view = resolve(reverse('recipes:home'))
        self.assertIs(view.func, views.home)

    def test_recipe_home_view_return_status_200_OK(self):
        response = self.client.get(reverse('recipes:home'))
        self.assertEqual(response.status_code, 200)

    def test_recipe_home_view_loads_correct_template(self):
        response = self.client.get(reverse('recipes:home'))
        self.assertTemplateUsed(response, 'recipes/pages/home.html')

    def test_recipe_home_shows_msg_if_no_recipes_found(self):
        response = self.client.get(reverse('recipes:home'))
        self.assertIn(
            'No recipes found here 🙁',
            response.content.decode('utf-8')
        )

    def test_recipe_home_template_loads_recipes(self):
        RecipeTestBase.make_recipe(self)
        response = self.client.get(reverse('recipes:home'))
        response_context = response.context['recipes']
        content = response.content.decode('utf-8')

        self.assertIn('Recipe title', content)
        self.assertIn('10 Minutos', content)
        self.assertIn('5 Porções', content)
        self.assertEqual(len(response_context), 1)

    def test_recipe_detail_view_func_is_correct(self):
        view = resolve(
            reverse('recipes:recipe', kwargs={'id': 1, })
        )
        self.assertIs(view.func, views.recipe)

    def test_recipe_detail_view_return_404_if_no_recipe_found(self):
        response = self.client.get(
            reverse('recipes:recipe', kwargs={'id': 999, })
        )
        self.assertEqual(response.status_code, 404)

    def test_recipe_category_view_func_is_correct(self):
        view = resolve(
            reverse('recipes:category', kwargs={'category_id': 1, })
        )
        self.assertIs(view.func, views.category)

    def test_recipe_category_view_return_404_if_no_recipes_found(self):
        response = self.client.get(
            reverse('recipes:category', kwargs={'category_id': 999, })
        )
        self.assertEqual(response.status_code, 404)
