import requests
from django.core.management.base import BaseCommand
from core.models import Genre, Movie
from requests.exceptions import RequestException
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Load new movies from TMDB API that haven't been uploaded yet"

    def add_arguments(self, parser):
        parser.add_argument('--total-movies', type=int, default=100, help='Number of movies to load')
        parser.add_argument('--endpoint', type=str, default='top_rated', 
                           choices=['popular', 'top_rated', 'now_playing'],
                           help='TMDB endpoint to fetch movies from')

    def handle(self, *args, **kwargs):
        API_KEY = "adc24b98ef40c36d560b5ef281b8cc64"
        total_movies = kwargs['total_movies']
        endpoint = kwargs['endpoint']
        movies_per_page = 20
        pages = (total_movies + movies_per_page - 1) // movies_per_page  # Ceiling division
        loaded_count = 0

        # Fetch genres once
        try:
            genre_response = requests.get(
                f"https://api.themoviedb.org/3/genre/movie/list?api_key={API_KEY}",
                timeout=5
            )
            genre_response.raise_for_status()
            genre_map = {g["id"]: g["name"] for g in genre_response.json()["genres"]}
            logger.info(f"Fetched {len(genre_map)} genres")
        except RequestException as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch genres: {e}"))
            return

        # Get existing TMDB IDs to avoid duplicates
        existing_tmdb_ids = set(Movie.objects.filter(tmdb_id__isnull=False).values_list('tmdb_id', flat=True))
        logger.info(f"Found {len(existing_tmdb_ids)} existing movies in database")

        for page in range(1, pages + 1):
            for attempt in range(3):  # Retry up to 3 times
                try:
                    response = requests.get(
                        f"https://api.themoviedb.org/3/movie/{endpoint}?api_key={API_KEY}&language=en-US&page={page}",
                        timeout=5
                    )
                    response.raise_for_status()
                    data = response.json()

                    for movie_data in data["results"]:
                        if loaded_count >= total_movies:
                            break

                        # Skip if movie already exists or lacks required fields
                        if movie_data["id"] in existing_tmdb_ids or not movie_data.get("poster_path") or not movie_data.get("release_date"):
                            continue

                        try:
                            # Create movie
                            movie, created = Movie.objects.get_or_create(
                                tmdb_id=movie_data["id"],
                                defaults={
                                    "title": movie_data["title"],
                                    "description": movie_data["overview"],
                                    "release_year": int(movie_data["release_date"].split("-")[0]),
                                    "rating": movie_data["vote_average"],
                                    "poster_url": f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}",
                                }
                            )
                            if not created:
                                continue  # Skip if movie was already in the database (edge case)

                            # Add genres
                            for genre_id in movie_data["genre_ids"]:
                                if genre_id in genre_map:
                                    genre, _ = Genre.objects.get_or_create(name=genre_map[genre_id])
                                    movie.genres.add(genre)

                            existing_tmdb_ids.add(movie_data["id"])
                            loaded_count += 1
                            self.stdout.write(self.style.SUCCESS(f"Added movie: {movie.title} (TMDB ID: {movie.tmdb_id})"))

                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error adding movie {movie_data['title']}: {e}"))

                    break  # Exit retry loop on success

                except RequestException as e:
                    self.stdout.write(self.style.WARNING(f"Request failed for page {page} (attempt {attempt + 1}): {e}"))
                    if attempt < 2:
                        time.sleep(2)
                    else:
                        self.stdout.write(self.style.ERROR(f"Failed to fetch page {page} after 3 attempts"))
                        break

            if loaded_count >= total_movies:
                break

        self.stdout.write(self.style.SUCCESS(f"Finished loading {loaded_count} new movies"))