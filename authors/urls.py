from django.urls import path
from authors import views

app_name = 'authors'

urlpatterns = [
    path('register/', views.register, name="register"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('dashboard/recipe/new/', views.recipe_create, name="recipe_create"),
    path('dashboard/recipe/<int:id>/edit/',
         views.recipe_edit, name="recipe_edit"),
    path('dashboard/recipe/<int:id>/delete/',
         views.recipe_delete, name="recipe_delete"),
]
