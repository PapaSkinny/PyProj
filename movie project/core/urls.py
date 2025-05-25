from django.urls import path
from core.views import MovieListView, register_view
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', MovieListView.as_view(), name='movie_list'),
    path('login/', LoginView.as_view(template_name='core/login.html'), name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='movie_list'), name='logout'),
    path('rate/<int:pk>/', views.rate_movie, name='rate_movie'),
    path('remove-rating/<int:pk>/', views.remove_rating, name='remove_rating'),
    path('rated/', views.rated_movies_view, name='rated_movies'), 
    path('recommend/', views.recommend_view, name='recommend'),
]