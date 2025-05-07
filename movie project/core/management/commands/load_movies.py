import requests
from django.core.management.base import BaseCommand
from core.models import Genre, Movie

class Command(BaseCommand):
    help = "Load movies from TMDB API"

    def handle(self, *args, **kwargs):
        API_KEY = "adc24b98ef40c36d560b5ef281b8cc64"
        total_movies = 100  # Сколько фильмов загрузить
        movies_per_page = 20  # Фильмов на страницу (макс. 20)
        pages = total_movies # movies_per_page

        for page in range(1, pages + 1):
            # Запрос списка популярных фильмов
            response = requests.get(
                f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=en-US&page={page}"
            )
            data = response.json()

            for movie_data in data["results"]:
                try:
                    # Пропустить фильмы без постера или года выпуска
                    if not movie_data.get("poster_path") or not movie_data.get("release_date"):
                        continue

                    # Создать фильм
                    movie, created = Movie.objects.get_or_create(
                        title=movie_data["title"],
                        defaults={
                            "description": movie_data["overview"],
                            "release_year": movie_data["release_date"].split("-")[0],
                            "rating": movie_data["vote_average"],
                            "poster_url": f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}",
                        }
                    )

                    # Добавить жанры
                    for genre_id in movie_data["genre_ids"]:
                        genre_response = requests.get(
                            f"https://api.themoviedb.org/3/genre/movie/list?api_key={API_KEY}"
                        )
                        for genre_data in genre_response.json()["genres"]:
                            if genre_data["id"] == genre_id:
                                genre, _ = Genre.objects.get_or_create(name=genre_data["name"])
                                movie.genres.add(genre)

                    self.stdout.write(self.style.SUCCESS(f"Добавлен фильм: {movie.title}"))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))