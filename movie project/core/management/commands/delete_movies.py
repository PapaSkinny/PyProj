from django.core.management.base import BaseCommand
from core.models import Movie, Rating, Genre

class Command(BaseCommand):
    help = "Delete all movies and optionally ratings and unused genres"

    def add_arguments(self, parser):
        parser.add_argument('--delete-ratings', action='store_true', help='Also delete all ratings')
        parser.add_argument('--delete-unused-genres', action='store_true', help='Delete genres with no associated movies')

    def handle(self, *args, **kwargs):
        delete_ratings = kwargs['delete_ratings']
        delete_unused_genres = kwargs['delete_unused_genres']

        # Delete movies
        movie_count = Movie.objects.count()
        Movie.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {movie_count} movies"))

        # Delete ratings if specified
        if delete_ratings:
            rating_count = Rating.objects.count()
            Rating.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {rating_count} ratings"))

        # Delete unused genres if specified
        if delete_unused_genres:
            genre_count = Genre.objects.filter(movie__isnull=True).count()
            Genre.objects.filter(movie__isnull=True).delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {genre_count} unused genres"))