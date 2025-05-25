from django.http import HttpResponse, JsonResponse

from django.views.generic import ListView
from core.models import Movie

from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegisterForm
from .forms import MovieFilterForm #filter for
from .models import Rating, Movie

from django.db.models import OuterRef, Subquery, IntegerField, Value
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

from surprise import SVD, Dataset, Reader
from collections import defaultdict
import numpy as np
import pandas as pd




# from django.db.models import Avg, Count
# from sklearn.metrics.pairwise import cosine_similarity
# from django.core.cache import cache
# import logging
# from django.db.models import Case, When

#from django.contrib.auth.forms import UserCreationForm


class MovieListView(ListView):
    model = Movie
    template_name = 'core/movie_list.html'
    context_object_name = 'movies'
    paginate_by = 48  # По 12 фильмов на странице
    ordering = ['-rating']  # Пример сортировки     d

    def get_queryset(self):
        queryset = Movie.objects.all()

        # Handle search
        search_query = self.request.GET.get('search') # url/search=
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        genre_id = self.request.GET.get('genre') # url/genre=
        sort_by = self.request.GET.get('sort_by') # url/genre=

        if genre_id:
            queryset = queryset.filter(genres__id=genre_id)

        if sort_by:
            queryset = queryset.order_by(sort_by)

        if self.request.user.is_authenticated:
            queryset = queryset.prefetch_related(Prefetch('ratings',queryset=Rating.objects.filter(user=self.request.user),to_attr='user_rating_list'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = MovieFilterForm(self.request.GET)

        # Добавим user_score каждому фильму
        if self.request.user.is_authenticated:
            for movie in context['movies']:
                if hasattr(movie, 'user_rating_list') and movie.user_rating_list:
                    movie.user_score = movie.user_rating_list[0].score
                else:
                    movie.user_score = None

        return context



class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user=True
    success_url=reverse_lazy("movie_list")

    def get_success_url(self):
        return self.success_url
    

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            print("✅ Регистрация успешна, редирект на главную.")
            return redirect('movie_list')
        else:
            #return render(request, 'core/register.html', {'form': form})
            print("❌ Форма невалидна:", form.errors)
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def rate_movie(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    score_str = request.POST.get('score')
    try:
        score = float(score_str)  # Convert to float to allow decimals
        if 0 <= score <= 10:      # Validate the range
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={'score': score}
            )
            return JsonResponse({
                'status': 'success',
                'message': 'Rating saved successfully',
                'score': score,
                'movie_id': movie.pk
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Score must be between 0 and 10'
            }, status=400)
    except (ValueError, TypeError):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid score value'
        }, status=400)

@login_required
def rated_movies_view(request):
    user_ratings = Rating.objects.filter(user=request.user).select_related('movie')
    
    # Create a dictionary of movie_id: rating for easy lookup
    rating_dict = {rating.movie.pk: rating.score for rating in user_ratings}
    
    # Get all rated movies
    rated_movies = [rating.movie for rating in user_ratings]

    genre_id = request.GET.get('genre')
    sort_by = request.GET.get('sort_by')

    if genre_id:
        rated_movies = [m for m in rated_movies if str(genre_id) in [str(g.id) for g in m.genres.all()]]

    if sort_by:
        rated_movies.sort(key=lambda m: getattr(m, sort_by), reverse=sort_by.startswith('-'))

    return render(request, 'core/rated_movies.html', {
        'rated_movies': rated_movies,
        'rating_dict': rating_dict,  # Pass the rating dictionary to template
        'filter_form': MovieFilterForm(request.GET)
    })

@login_required
def remove_rating(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    Rating.objects.filter(user=request.user, movie=movie).delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',    
            'message': 'Rating removed successfully'
        })
    return redirect('movie_list')

# logger = logging.getLogger(__name__)

@login_required
def recommend_view(request):
    user = request.user

    # Получаем все оценки
    ratings = Rating.objects.all().values_list('user__id', 'movie__id', 'score')

    if not ratings:
        return render(request, 'core/recommendations.html', {
            'recommendations': [],
            'message': 'Нет данных для рекомендаций.'
        })

    # Обучение SVD
    reader = Reader(rating_scale=(0, 10))
    data = Dataset.load_from_df(
        pd.DataFrame(ratings, columns=["userID", "itemID", "rating"]),
        reader
    )
    trainset = data.build_full_trainset()
    model = SVD()
    model.fit(trainset)

    # Фильмы, которые пользователь уже оценивал
    rated_movie_ids = set(
        Rating.objects.filter(user=user).values_list('movie_id', flat=True)
    )

    # Предсказания для всех фильмов, которые пользователь НЕ оценивал
    all_movie_ids = Movie.objects.values_list('id', flat=True)
    candidates = [mid for mid in all_movie_ids if mid not in rated_movie_ids]

    predictions = []
    for movie_id in candidates:
        pred = model.predict(uid=user.id, iid=movie_id)
        predictions.append((movie_id, pred.est))

    # Сортировка по убыванию предсказанного рейтинга
    predictions.sort(key=lambda x: x[1], reverse=True)
    top_movie_ids = [pid for pid, _ in predictions[:12]]  # топ 12 рекомендаций

    recommended_movies = Movie.objects.filter(id__in=top_movie_ids)

    # Сохраняем порядок вручную
    movie_order = {id_: i for i, id_ in enumerate(top_movie_ids)}
    recommended_movies = sorted(recommended_movies, key=lambda m: movie_order[m.id])

    return render(request, 'core/recommendations.html', {
        'recommendations': recommended_movies
    })