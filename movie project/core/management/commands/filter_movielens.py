import pandas as pd
from django.core.management.base import BaseCommand
from core.models import Movie
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Filter MovieLens 1M ratings to only include movies in the database"

    def add_arguments(self, parser):
        parser.add_argument('--data-path', type=str, default='core/data/ml-1m/', help='Path to MovieLens 1M data folder')
        parser.add_argument('--links-file', type=str, default='core/data/ml-1m/links.csv', help='Path to links.csv')
        parser.add_argument('--output-file', type=str, default='core/data/ml-1m/filtered_ratings.csv', 
                           help='Output file for filtered ratings')

    def handle(self, *args, **kwargs):
        data_path = kwargs['data_path']
        links_file = kwargs['links_file']
        output_file = kwargs['output_file']

        # Load MovieLens links and ratings
        try:
            links_df = pd.read_csv(links_file)
            ratings_df = pd.read_csv(f"{data_path}/ratings.dat", sep='::', engine='python',
                                    names=['userId', 'movieId', 'rating', 'timestamp'])
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"File not found: {e}"))
            return

        # Get TMDB IDs from database
        db_tmdb_ids = set(Movie.objects.filter(tmdb_id__isnull=False).values_list('tmdb_id', flat=True))
        logger.info(f"Found {len(db_tmdb_ids)} movies in database")

        # Filter to common movies
        links_df['tmdbId'] = links_df['tmdbId'].dropna().astype(float)
        common_tmdb_ids = db_tmdb_ids.intersection(set(links_df['tmdbId']))
        logger.info(f"Found {len(common_tmdb_ids)} common movies")

        if not common_tmdb_ids:
            self.stdout.write(self.style.ERROR("No common movies found"))
            return

        common_movie_ids = links_df[links_df['tmdbId'].isin(common_tmdb_ids)]['movieId']
        filtered_ratings = ratings_df[ratings_df['movieId'].isin(common_movie_ids)]

        # Save filtered ratings
        filtered_ratings.to_csv(output_file, index=False)
        logger.info(f"Saved {len(filtered_ratings)} ratings to {output_file}")
        self.stdout.write(self.style.SUCCESS(f"Filtered {len(filtered_ratings)} ratings for {len(common_movie_ids)} movies"))