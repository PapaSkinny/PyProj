
from django.db import models
from django.contrib.auth.models import User

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True, null=True) 
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    release_year = models.IntegerField()
    rating = models.FloatField(default=0.0)
    poster_url = models.URLField(blank=True)
    genres = models.ManyToManyField(Genre)  # Связь многие-ко-многим

    def __str__(self):
        return self.title
    

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    #score = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(11)])  # Оценки от 0 до 10
    score = models.FloatField(default=0.0)
    def __str__(self):
        return f'{self.movie.title} - {self.score}'
    class Meta:
        unique_together = ('user', 'movie')