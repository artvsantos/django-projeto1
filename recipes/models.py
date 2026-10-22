from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=65)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    title = models.CharField(max_length=65)
    description = models.CharField(max_length=165)
    slug = models.SlugField(unique=True)
    preparation_time = models.IntegerField()
    preparation_time_unit = models.CharField(max_length=65)
    servings = models.IntegerField()
    servings_unit = models.CharField(max_length=65)
    preparation_steps = models.TextField()
    preparation_steps_is_html = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    cover = models.ImageField(
        upload_to='recipes/covers/%Y/%m/%d/', blank=True, default='',
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        default=None,
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Receita criada pelo painel do autor chega sem slug. Ele é gerado
        # uma vez só: mudar o título depois não quebra links já divulgados.
        if not self.slug:
            self.slug = self._unique_slug()
        return super().save(*args, **kwargs)

    def _unique_slug(self):
        # SlugField tem 50 caracteres; sobra espaço para o sufixo "-2", "-3".
        base = slugify(self.title)[:45].strip('-') or 'receita'
        slug, number = base, 2
        while Recipe.objects.filter(slug=slug).exists():
            slug = f'{base}-{number}'
            number += 1
        return slug
