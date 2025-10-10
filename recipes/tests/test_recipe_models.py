from django.core.exceptions import ValidationError
from .test_recipe_base import RecipeTestBase, Recipe
from parameterized import parameterized


class RecipesModelsTests(RecipeTestBase):
    def setUp(self) -> None:
        self.recipe = self.make_recipe()
        self.categy = self.make_category()
        return super().setUp()

    def make_recipe_no_default(self):
        recipe = Recipe(
            category=self.make_category('Default Category'),
            author=self.make_author(username='Jouse'),
            title='Recipe title',
            description='Recipe description',
            slug='recipe-slug-default',
            preparation_time=10,
            preparation_time_unit='Minutos',
            servings=5,
            servings_unit='Porções',
            preparation_steps='Recipe preparation steps',
        )
        recipe.full_clean()
        recipe.save()
        return recipe

    @parameterized.expand([
        ('title', 65),
        ('description', 165),
        ('preparation_time_unit', 65),
        ('servings_unit', 65),
    ])
    def test_recipe_model_fields_max_length(self, field, max_length):
        setattr(self.recipe, field, 'A' * (max_length + 1))

        with self.assertRaises(ValidationError):
            self.recipe.full_clean()

    def test_recipe_preparation_steps_is_html_is_false_by_default(self):
        recipe = self.make_recipe_no_default()

        self.assertFalse(
            recipe.preparation_steps_is_html,
            msg='preparation_steps_is_html is not False'
        )

    def test_recipe_is_published_is_false_by_default(self):
        recipe = self.make_recipe_no_default()

        self.assertFalse(
            recipe.is_published,
            msg='is_published is not False'
        )

    def test_recipe_str_title_represetation(self):
        self.recipe.title = 'Testing represetation'
        self.recipe.full_clean()
        self.recipe.save()
        self.assertEqual(str(self.recipe), 'Testing represetation')

    def test_recipe_str_category_represetation(self):
        self.categy.name = 'Testing represetation category'
        self.categy.full_clean()
        self.categy.save()
        self.assertEqual(str(self.categy), 'Testing represetation category')

    def test_recipe_category_model_name_max_lenght_is_65_chars(self):
        self.categy.name = "a" * 66
        with self.assertRaises(ValidationError):
            self.categy.full_clean()
