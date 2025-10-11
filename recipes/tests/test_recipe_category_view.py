from django.urls import reverse, resolve
from .test_recipe_base import RecipeTestBase
from recipes import views

# Create your tests here.


class RecipeCategoryViewTest(RecipeTestBase):

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

    def test_recipe_category_template_dont_load_is_publishe_false(self):
        recipe = self.make_recipe(is_published=False)
        response = self.client.get(
            reverse('recipes:recipe', kwargs={
                    'id': recipe.category.id})  # type: ignore
        )
        self.assertEqual(response.status_code, 404)

    def test_recipe_category_template_loads_recipes(self):
        self.make_recipe()
        response = self.client.get(reverse('recipes:category', args=(1,)))
        content = response.content.decode('utf-8')

        self.assertIn('Category', content)
