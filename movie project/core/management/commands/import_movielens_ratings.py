import pandas as pd
from django.core.management.base import BaseCommand
from core.models import Rating, Movie
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Import filtered MovieLens 1M ratings for Django users"

    def add_arguments(self, parser):
        parser.add_argument('--ratings-file', type=str, default='core/data/ml-1m/filtered_ratings.csv', 
                           help='Path to filtered ratings CSV')
        parser.add_argument('--links-file', type=str, default='core/data/ml-1m/links.csv', 
                           help='Path to MovieLens links.csv')
        parser.add_argument('--max-ratings-per-user', type=int, default=200, 
                           help='Max ratings per user')

    def handle(self, *args, **kwargs):
        ratings_file = kwargs['ratings_file']
        links_file = kwargs['links_file']
        max_ratings = kwargs['max_ratings_per_user']
        total_added = 0

        # Load data
        ratings_df = pd.read_csv(ratings_file)
        links_df = pd.read_csv(links_file)
        movie_id_to_tmdb = dict(zip(links_df['movieId'], links_df['tmdbId'].astype(float)))

        # Map Django users to MovieLens users
        django_users = User.objects.all()[:3]
        if len(django_users) < 3:
            self.stdout.write(self.style.ERROR("Need at least 3 Django users"))
            return

        user_mapping = {i + 1: user for i, user in enumerate(django_users)}

        for ml_user_id in [1, 2, 3]:
            if ml_user_id not in user_mapping:
                continue
            django_user = user_mapping[ml_user_id]
            user_ratings = ratings_df[ratings_df['userId'] == ml_user_id].head(max_ratings)

            for _, row in user_ratings.iterrows():
                tmdb_id = movie_id_to_tmdb.get(row['movieId'])
                if not tmdb_id:
                    continue

                try:
                    movie = Movie.objects.get(tmdb_id=tmdb_id)
                    rating, created = Rating.objects.get_or_create(
                        user=django_user,
                        movie=movie,
                        defaults={'score': row['rating'] * 2}  # Scale 1–5 to 0–10
                    )
                    if created:
                        total_added += 1
                        self.stdout.write(self.style.SUCCESS(f"Added rating for {django_user.username} on {movie.title}: {rating.score}"))
                except Movie.DoesNotExist:
                    continue

        self.stdout.write(self.style.SUCCESS(f"Added {total_added} new ratings"))
        logger.info(f"Total ratings in database: {Rating.objects.count()}")