
from django.http import HttpResponse

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

#from django.contrib.auth.forms import UserCreationForm


class MovieListView(ListView):
    model = Movie
    template_name = 'core/movie_list.html'
    context_object_name = 'movies'
    paginate_by = 48  # По 12 фильмов на странице
    ordering = ['-rating']  # Пример сортировки     

    def get_queryset(self):
        queryset = Movie.objects.all()

        genre_id = self.request.GET.get('genre')
        sort_by = self.request.GET.get('sort_by')

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
                    movie.user_score = 0

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
    score = request.POST.get('score')

    # Проверка, что оценка находится в пределах от 0 до 10
    if score and 0 <= int(score) <= 10:
        score = int(score)

        # Если оценка уже существует, обновляем её, иначе создаём новую
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={'score': score}
        )
    else:
        # Если некорректная оценка, перенаправляем на страницу с ошибкой
        return redirect('movie_list')

    return redirect('movie_list')

@login_required
def rated_movies_view(request):
    user_ratings = Rating.objects.filter(user=request.user).select_related('movie')
    rated_movies = [rating.movie for rating in user_ratings]

    genre_id = request.GET.get('genre')
    sort_by = request.GET.get('sort_by')

    if genre_id:
        rated_movies = [m for m in rated_movies if str(genre_id) in [str(g.id) for g in m.genres.all()]]

    if sort_by:
        rated_movies.sort(key=lambda m: getattr(m, sort_by), reverse=sort_by.startswith('-'))

    return render(request, 'core/rated_movies.html', {
        'rated_movies': rated_movies,
        'filter_form': MovieFilterForm(request.GET)
    })


