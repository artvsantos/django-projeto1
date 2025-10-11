from django.urls import reverse, resolve
from .test_recipe_base import RecipeTestBase
from recipes import views

# Create your tests here.


class RecipeDetailViewTest(RecipeTestBase):

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

    def test_recipe_detail_template_loads_recipes(self):
        needed_title = 'This is a detail page - It load one recipe'
        self.make_recipe(title=needed_title)
        response = self.client.get(reverse('recipes:recipe', args=(1,)))
        content = response.content.decode('utf-8')

        self.assertIn(needed_title, content)

    def test_recipe_detail_template_dont_load_is_publishe_false(self):
        recipe = self.make_recipe(is_published=False)
        response = self.client.get(
            reverse('recipes:recipe', kwargs={
                    'id': recipe.id})  # type: ignore
        )
        self.assertEqual(response.status_code, 404)
