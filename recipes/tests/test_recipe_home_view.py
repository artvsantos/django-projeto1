from django.urls import reverse, resolve
from .test_recipe_base import RecipeTestBase
from recipes import views


class RecipeHomeViewTest(RecipeTestBase):
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
        self.make_recipe()
        response = self.client.get(reverse('recipes:home'))
        response_context = response.context['recipes']
        content = response.content.decode('utf-8')

        self.assertIn('Recipe title', content)
        self.assertIn('10 Minutos', content)
        self.assertIn('5 Porções', content)
        self.assertEqual(len(response_context), 1)

    def test_recipe_home_template_dont_load_is_publishe_false(self):
        self.make_recipe(is_published=False)
        response = self.client.get(reverse('recipes:home'))

        self.assertIn(
            'No recipes found here 🙁',
            response.content.decode('utf-8')
        )
