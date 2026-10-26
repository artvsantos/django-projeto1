from django.urls import path
from rest_framework.routers import APIRootView, DefaultRouter

from api import views

app_name = 'api'


class ApiRootView(APIRootView):
    """Endereços da API.

    Ler receitas e categorias é aberto a todos. Para criar e editar as suas
    em my-recipes/, peça um token com POST em /api/v1/token/ e mande no
    cabeçalho: Authorization: Token <seu token>
    """

    def get_view_name(self):
        return 'API do Receitas'


class Router(DefaultRouter):
    APIRootView = ApiRootView


router = Router()
router.register('recipes', views.RecipeViewSet, basename='recipe')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('my-recipes', views.MyRecipeViewSet, basename='my-recipe')

urlpatterns = [
    path('token/', views.TokenView.as_view(), name='token'),
] + router.urls
