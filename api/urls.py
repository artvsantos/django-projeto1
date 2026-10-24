from rest_framework.routers import APIRootView, DefaultRouter

from api import views

app_name = 'api'


class ApiRootView(APIRootView):
    """Endereços disponíveis. Tudo é só leitura e não precisa de login."""

    def get_view_name(self):
        return 'API do Receitas'


class Router(DefaultRouter):
    APIRootView = ApiRootView


router = Router()
router.register('recipes', views.RecipeViewSet, basename='recipe')
router.register('categories', views.CategoryViewSet, basename='category')

urlpatterns = router.urls
